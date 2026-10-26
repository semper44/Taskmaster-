import hashlib
import os
import queue
import signal
import shlex
import subprocess
import json
import threading
from pathlib import Path
import time

from http.client import HTTPConnection, HTTPException
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
from contextlib import contextmanager
from tempfile import TemporaryDirectory

from django.conf import settings
from django.db import close_old_connections, transaction

from brimble.consumers import (
    prune_persisted_log_batches,
    reserve_log_persist_offset,
    send_deployment_log_chunk,
    send_deployment_update,
)
from .models import Deployment


# Keep live WebSocket frames small and frequent, while making database writes
# less frequent. These are deliberately separate buffers: the browser's latency
# does not have to wait for a database write.
LIVE_LOG_FLUSH_SECONDS = 0.1 #100 ms my buffer should wait
LIVE_LOG_MAX_CHARS = 16 * 1024
PERSIST_LOG_FLUSH_SECONDS = 0.25
PERSIST_LOG_MAX_LINES = 20


class CaddyReloadError(RuntimeError):
    """A route reload failed after the deployment container was already healthy."""


def cleanup_failed_deployment_container(deployment, error):
    """Remove failed deployment containers, but keep healthy apps after Caddy errors."""

    if not deployment.container_name or isinstance(error, CaddyReloadError):
        return

    try:
        cleanup_result = subprocess.run(
            ["docker", "rm", "-f", deployment.container_name],
            check=False,
            capture_output=True,
            text=True,
            timeout=30,
        )
        if cleanup_result.returncode != 0 and cleanup_result.stderr.strip():
            print(
                f"[DEPLOYMENT {deployment.id}] Container cleanup warning: "
                f"{cleanup_result.stderr.strip()}",
                flush=True,
            )
    except (OSError, subprocess.TimeoutExpired) as cleanup_error:
        print(
            f"[DEPLOYMENT {deployment.id}] Container cleanup failed: {cleanup_error}",
            flush=True,
        )



# Immediate check whether the container is running, so the hostport can be gotten.
def ensure_container_running(container_name):
    """Fail with the container exit code before trying to inspect its port."""

    result = subprocess.run(
        [
            "docker",
            "inspect",
            "--format",
            "{{.State.Running}}|{{.State.ExitCode}}",
            container_name,
        ],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Could not inspect container {container_name}: {result.stderr.strip()}")

    running, exit_code = result.stdout.strip().split("|", 1)
    if running.lower() != "true":
        raise RuntimeError(f"Container exited before port lookup. Exit code: {exit_code}")


def wait_for_readiness(deployment_id, container_name, host_port, timeout=120):
    """
    Wait until the deployed application returns an HTTP response below 500.

    INPUT:
        deployment_id: Primary key of the Deployment.
        container_name: Name of the Docker container.
        host_port: Host port published for the app's container port.
        timeout: Maximum number of seconds to wait.

    OUTPUT:
        True if the application becomes ready.

    Raises:
        RuntimeError if the container exits or readiness times out.
    """

    deadline = time.monotonic() + timeout
    last_response = "the application has not responded yet"

    while time.monotonic() < deadline:
        # a timely check whether Django is still running.
        ensure_container_running(container_name)
        connection = HTTPConnection("127.0.0.1", host_port, timeout=2)
        try:
            connection.request("GET", "/")
            response = connection.getresponse()
            if response.status < 500:
                #print(f"[DEPLOYMENT {deployment_id}] Application responded with HTTP {response.status}.",flush=True,)
                return True
            last_response = f"HTTP {response.status}"
        except (OSError, HTTPException) as error:
            last_response = str(error)
        finally:
            connection.close()

        time.sleep(min(2, max(0, deadline - time.monotonic())))

    raise RuntimeError(
        f"Application did not become ready within {timeout} seconds. "
        f"Last HTTP probe result: {last_response}."
    )


# for some needed build packges for docker that are absent in the image
def write_railpack_config(work_dir):
    """Write Brimble's default runtime packages into the build directory."""
    config = {
        "$schema": "https://schema.railpack.com",
        "deploy": {
            "aptPackages": [
                "...",
                "libffi8",
                "libssl3",
                "libpq5",
                "libstdc++6",
                "libgomp1",
                "ca-certificates",
                "curl",
                "tzdata",
            ]
        },
    }

    config_path = Path(work_dir) / "railpack.json"
    config_path.write_text(
        json.dumps(config, indent=2),
        encoding="utf-8",
    )

    #print(f"Railpack configuration written to: {config_path}")


@shared_task(name="projects.stream_deployment_log_chunk")
def stream_deployment_log_chunk(deployment_id, chunk):
    """Send a live log chunk to the browser through the deployment WebSocket group."""

    send_deployment_log_chunk(deployment_id, chunk)


@shared_task(bind=True, name="projects.persist_deployment_log_batch")
def persist_deployment_log_batch(self, deployment_id, chunk, start_offset):
    """Append a batch at its reserved offset so parallel workers cannot reorder logs."""

    close_old_connections()
    with transaction.atomic():
        deployment = Deployment.objects.select_for_update().get(pk=deployment_id)
        saved_logs = deployment.logs or ""
        already_persisted = False
        if len(saved_logs) < start_offset:
            # Earlier log text is still missing from the database; wait and retry.
            raise self.retry(countdown=0.2, max_retries=100)
        if len(saved_logs) > start_offset:
            # The database passed this batch's start; skip only if this exact text is already there.
            if saved_logs[start_offset:start_offset + len(chunk)] == chunk:
                already_persisted = True
            else:
                raise ValueError(f"Log persistence offset conflict for deployment {deployment_id}")

        # if len(saved_logs) == start_offset
        if not already_persisted:
            deployment.logs = saved_logs + chunk
            deployment.save(update_fields=["logs", "updated_at"])
    # Once the DB contains a prefix, its matching Redis replay chunks are no
    # longer needed. Keeping only the unsaved tail for reconnects.
    try:
        prune_persisted_log_batches(deployment_id, len(deployment.logs))
    except Exception as error:
        # Persistence must remain successful even if Redis cleanup is unavailable.
        print(f"Could not prune replay logs for deployment {deployment_id}: {error}", flush=True)



def queue_deployment_log_persist(deployment_id, chunk):
    """Reserve a stable DB position, then let Celery persist the batch asynchronously."""
    if not chunk:
        return
    start_offset = reserve_log_persist_offset(deployment_id, len(chunk))
    persist_deployment_log_batch.delay(deployment_id, chunk, start_offset)


def start_deployment(deployment_id):
    """Queue deployment work in Celery and return immediately to the API caller.

        Only the deployment ID is sent through Redis. The Celery worker loads a fresh
        Django record when it begins, rather than serializing a model object.
    """
    #print("start_deploy-111")
    run_deployment.delay(deployment_id)
    #print("start_deploy-222")
   



def _terminate_process_tree(process, grace_period=5):
    """Stop a command and, on POSIX, any child processes it started."""

    if os.name == "posix":
        # Popen starts this command in a new session, so its process group is
        # isolated from the Celery worker and can be stopped as one unit.
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=grace_period)
        except subprocess.TimeoutExpired:
            pass

        # Kill anything in the group that ignored the graceful signal. The
        # parent may already have exited while one of its children is alive.
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
    elif process.poll() is None:
        process.terminate()
        try:
            process.wait(timeout=grace_period)
        except subprocess.TimeoutExpired:
            process.kill()

    try:
        process.wait(timeout=grace_period)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def run_command(deployment_id, command, cwd=None, env=None, timeout=15 * 60):
    """Run a command, stream its output into the deployment log, and return its exit code.

        A return code of zero conventionally means success. Any non-zero value is
        interpreted by the caller as a failed pipeline step.
    """

    
    # Displaying commands that are ran
    command_prefix = f"$ {shlex.join(command)}\n"
    # Send the command line to connected browsers right away, then queue a
    # separate database save. The browser does not wait for Celery to save it.
    send_deployment_log_chunk(deployment_id, command_prefix)
    queue_deployment_log_persist(deployment_id, command_prefix)
    try:
        # These options put the child command in its own process group. If the
        # command times out, _terminate_process_tree can stop it and its children
        # without accidentally stopping the Celery worker itself.
        popen_options = {}
        if os.name == "posix":
            popen_options["start_new_session"] = True
        elif os.name == "nt":
            popen_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        # Popen starts the external program and gives us its process handle.
        # stdout is piped back to Python; stderr is merged into stdout so build
        # errors appear in the same ordered log stream as normal output.
        # text=True makes each read a Python string, and bufsize=1 asks for
        # line-buffered reading on this side of the pipe.
        process = subprocess.Popen(
            command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            env=env,
            **popen_options,
        )
    except (FileNotFoundError, PermissionError, OSError) as e:
        error_msg = f"Failed to start command: {type(e).__name__}: {e}\n"
        send_deployment_log_chunk(deployment_id, error_msg)
        queue_deployment_log_persist(deployment_id, error_msg)
        #print(error_msg, flush=True)
        return 1
    
    if process.stdout is None:
        return process.wait()

    # The reader thread can wait on the subprocess pipe while the main thread
    # keeps checking timers, enforcing the timeout, and flushing log batches.
    # Celery runs this whole function as a background task; the thread is only
    # a small helper inside that one task, not another Celery worker/process.
    # A bounded queue limits memory if output arrives faster than we can send it.
    output_queue = queue.Queue(maxsize=100)
    stop_reader = threading.Event()

    def read_output():
        """Read and que child output without blocking the main batching/timer loop."""
        try:
            # Iterating over a text pipe yields one line at a time. A line is
            # available when the child writes a newline (or closes its output).
            for output_line in process.stdout:
                # If the queue is full, wait briefly and try again. The main
                # thread will make room as it takes lines out and batches them.
                while not stop_reader.is_set():
                    try:
                        output_queue.put(output_line, timeout=0.1)
                        # This line is now safely in the queue. Stop retrying it
                        # and move on to reading the next line from the process with break.
                        break
                    except queue.Full:
                        # The queue is temporarily full, not a fatal error.
                        # Retry unless cleanup has told this reader to stop.
                        continue
        except (OSError, ValueError):
            # The main thread can close the pipe while cleaning up a timeout.
            pass
        finally:
            # None is a marker meaning "there will be no more output lines".
            # It lets the main thread distinguish end-of-output from an empty
            # queue that simply has not received the next line yet.
            while not stop_reader.is_set():
                try:
                    output_queue.put(None, timeout=0.1)
                    break
                except queue.Full:
                    continue

    # Start the helper now. It waits for output while this main thread continues
    # below, so an idle child cannot prevent the timeout clock from being checked.
    reader = threading.Thread(target=read_output, daemon=True)
    reader.start()

    # The same output is collected twice for different destinations. a short
    # live batch for the WebSocket, and a separate batch for the database task.
    live_buffer = []
    live_buffer_chars = 0
    persist_buffer = []
    persist_buffer_lines = 0
    last_live_flush = time.monotonic()
    last_persist_flush = last_live_flush
    deadline = time.monotonic() + timeout
    timed_out = False
    completed = False

    def flush_live_buffer():
        """Send the accumulated live text as one WebSocket message."""
        nonlocal live_buffer_chars, last_live_flush
        if live_buffer:
            send_deployment_log_chunk(deployment_id, "".join(live_buffer))
            live_buffer.clear()
            live_buffer_chars = 0
        last_live_flush = time.monotonic()


    def flush_persist_buffer():
        """Queue the accumulated text for an independent database append."""
        nonlocal persist_buffer_lines, last_persist_flush
        if persist_buffer:
            queue_deployment_log_persist(deployment_id, "".join(persist_buffer))
            persist_buffer.clear()
            persist_buffer_lines = 0
        last_persist_flush = time.monotonic()

    try:
        while True:
            remaining = deadline - time.monotonic() #time until the command timeout
            if remaining <= 0:
                timed_out = True
                break


            # calculate the next flush deadline by subtracting the last flush time from the current time and subtracting that from the flush interval. 
            # if the result is negative, it means that the flush interval has already passed
            # so we return 0 to flush immediately. if it is positive, we return that value to wait until the next flush.
            until_live_flush = max(0, LIVE_LOG_FLUSH_SECONDS - (time.monotonic() - last_live_flush)) #using max, cos i want to return the remaining time if it is positive, otherwise, return zero.
            until_persist_flush = max(0, PERSIST_LOG_FLUSH_SECONDS - (time.monotonic() - last_persist_flush)) #same here

            try:
                # getting an output after a timeout
                line = output_queue.get(
                    timeout=min(
                        remaining,  # time until the command timeout
                        until_live_flush or 0.01,  # time until the browser buffer be checked
                        until_persist_flush or 0.01,  # time until the database buffer be checked
                    ) #min of the three values, so that minimum time is used, not the max. if until_live_flush is 0.02 and until_persist_flush is 2.5, it doesnt have to wait 2.5secs
                )

            
            except queue.Empty:
                flush_live_buffer()
                if time.monotonic() - last_persist_flush >= PERSIST_LOG_FLUSH_SECONDS:
                    flush_persist_buffer()
                continue

            if line is None:
                # The reader reached end-of-output and sent its marker. Leave the loop. the remaining buffers are flushed below.
                break

            # adding to buffer.
            print(f"[DEPLOYMENT {deployment_id}] {line}", end="", flush=True)
            live_buffer.append(line)
            live_buffer_chars += len(line)
            persist_buffer.append(line)
            persist_buffer_lines += 1

            if (time.monotonic() - last_live_flush >= LIVE_LOG_FLUSH_SECONDS
                    or live_buffer_chars >= LIVE_LOG_MAX_CHARS):
                flush_live_buffer()
            if (persist_buffer_lines >= PERSIST_LOG_MAX_LINES
                    or time.monotonic() - last_persist_flush >= PERSIST_LOG_FLUSH_SECONDS):
                flush_persist_buffer()

        if not timed_out:
            try:
                process.wait(timeout=max(0, deadline - time.monotonic()))
            except subprocess.TimeoutExpired:
                timed_out = True
            else:
                completed = True

        if timed_out:
            _terminate_process_tree(process)
            flush_live_buffer()
            flush_persist_buffer()
            timeout_msg = f"Command timed out after {timeout} seconds: {shlex.join(command)}\n"
            print(f"[DEPLOYMENT {deployment_id}] {timeout_msg}", end="", flush=True)
            send_deployment_log_chunk(deployment_id, timeout_msg)
            queue_deployment_log_persist(deployment_id, timeout_msg)
            return 124

        flush_live_buffer()
        flush_persist_buffer()
        print(f"[DEPLOYMENT {deployment_id}] COMMAND EXIT CODE: {process.returncode}", flush=True)
        return process.returncode
    finally:
        # This also runs if Celery's soft time limit interrupts the task.
        if not completed:
            _terminate_process_tree(process)
        stop_reader.set()
        reader.join(timeout=1)
        if reader.is_alive() and process.stdout:
            process.stdout.close()



def run_port(deployment_id, container_name):
    """Run, retrieve and print the published Docker port."""

    result = subprocess.run(
        ["docker", "port", container_name, "3000/tcp"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    output = (result.stdout or "") + (result.stderr or "")

    for line in output.splitlines():
        print(f"[DEPLOYMENT {deployment_id}] {line}", flush=True)

    if result.returncode != 0:
        print(
            f"[DEPLOYMENT {deployment_id}] "
            f"docker port failed with exit code {result.returncode}",
            flush=True,
        )
        raise RuntimeError(
            f"docker port failed with exit code {result.returncode}: "
            f"{(result.stderr or result.stdout).strip()}"
        )

    mappings = [line.strip() for line in result.stdout.splitlines() if line.strip()]
    if not mappings:
        raise RuntimeError(f"docker port returned no published port for {container_name}.")

    try:
        host_port = int(mappings[0].rsplit(":", 1)[-1])
    except ValueError as error:
        raise RuntimeError(f"Could not parse docker port output: {mappings[0]}") from error

    if not 1 <= host_port <= 65535:
        raise RuntimeError(f"Docker returned an invalid published port: {host_port}")
    return host_port



@contextmanager
def docker_registry_environment():
    """Use anonymous registry access unless a Docker config is explicitly supplied."""

    configured_docker_config = os.environ.get("BRIMBLE_DOCKER_CONFIG")
    if configured_docker_config:
        environment = os.environ.copy()
        environment["DOCKER_CONFIG"] = configured_docker_config
        yield environment
        return

    with TemporaryDirectory(prefix="brimble-docker-config-") as docker_config:
        environment = os.environ.copy()
        environment["DOCKER_CONFIG"] = docker_config
        yield environment


def ensure_buildkit(deployment_id, buildkit_name, environment=None):
    """Reuse this checkout's BuildKit container, starting it when stopped."""

    inspect_result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", buildkit_name],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if inspect_result.returncode == 0:
        if inspect_result.stdout.strip().lower() == "true":
            return
        if run_command(deployment_id, ["docker", "start", buildkit_name], env=environment) == 0:
            return
        raise RuntimeError("BuildKit restart failed")

    if run_command(
        deployment_id,
        [
            "docker",
            "run",
            "--privileged",
            "-d",
            "--name",
            buildkit_name,
            "-v",
            "brimble-buildkit-cache:/var/lib/buildkit",
            "moby/buildkit",
        ],
        env=environment,
    ) == 0:
        return

    inspect_result = subprocess.run(
        ["docker", "inspect", "--format", "{{.State.Running}}", buildkit_name],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if inspect_result.returncode == 0 and inspect_result.stdout.strip().lower() == "true":
        return
    raise RuntimeError("BuildKit startup failed")



def configure_caddy(application_route_id, deployment_id, host_port):
    """Switch a stable app route to its healthy container and reload Caddy."""

    caddyfile = Path(os.environ.get("CADDYFILE", Path(settings.BASE_DIR) / "Caddyfile"))
    caddyfile.parent.mkdir(parents=True, exist_ok=True)

    routes = []
    for item in Deployment.objects.filter(is_active=True).exclude(application_route_id=application_route_id):
        if item.host_port:
            routes.append(
                f"\thandle_path /apps/{item.application_route_id}/* {{\n"
                f"\t\treverse_proxy 127.0.0.1:{item.host_port}\n\t}}"
            )

    routes.append(
        f"\thandle_path /apps/{application_route_id}/* {{\n"
        f"\t\treverse_proxy 127.0.0.1:{host_port}\n\t}}"
    )
    deployment_ids = set(
        Deployment.objects.filter(application_route_id=application_route_id)
        .values_list("id", flat=True)
    )
    deployment_ids.add(deployment_id)
    for route_deployment_id in sorted(deployment_ids):
        routes.append(
            f"\thandle_path /deployments/{route_deployment_id}/* {{\n"
            f"\t\treverse_proxy 127.0.0.1:{host_port}\n\t}}"
        )
    caddyfile.write_text(":8080 {\n" + "\n".join(routes) + "\n}\n", encoding="utf-8")

    try:
        reload_result = subprocess.run(
            [os.environ.get("CADDY_BIN", "caddy"), "reload", "--config", str(caddyfile)],
            capture_output=True,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired) as error:
        message = f"Caddy reload failed: {error}"
        raise CaddyReloadError(message) from error

    if reload_result.returncode != 0:
        error = reload_result.stderr.strip() or reload_result.stdout.strip()
        raise CaddyReloadError(f"Caddy reload failed: {error}")

    log_line = reload_result.stdout.strip()
    print(log_line, end="", flush=True)
    send_deployment_log_chunk(deployment_id, log_line)
    queue_deployment_log_persist(deployment_id, log_line)

@shared_task(name="projects.run_deployment")
def run_deployment(deployment_id):
    """Execute the full deployment sequence as a Celery worker task."""

    #print("iii", deployment_id)
    close_old_connections()
    deployment = Deployment.objects.get(pk=deployment_id)
    work_dir = deployment.source_path or str(Path(settings.MEDIA_ROOT) / "deployments" / str(deployment.id))
    reuse_image = deployment.reused_from_id is not None
    image_tag = deployment.image_tag if reuse_image else f"brimble/deployment-{deployment.id}:latest"
    application_route_id = deployment.application_route_id or deployment.id
    deployment.application_route_id = application_route_id
    container_name = f"brimble-deployment-{deployment.id}"
    checkout_id = hashlib.sha256(str(Path(settings.BASE_DIR).resolve()).encode("utf-8")).hexdigest()[:12]
    buildkit_name = f"brimble-buildkit-{checkout_id}"
    #print("iii22")

    try:
        if reuse_image:
            image_check = subprocess.run(
                ["docker", "image", "inspect", image_tag],
                capture_output=True,
                text=True,
                timeout=15,
            )
            if image_check.returncode != 0:
                raise RuntimeError(f"Previously built image {image_tag} is not available locally.")
            deployment.status = Deployment.Status.DEPLOYING
            deployment.current_stage = "deploying"
            action_label = deployment.get_reused_deployment_type_display() or "Image reuse"
            deployment.current_message = f"{action_label}: starting container from image {image_tag}"
            deployment.save(update_fields=["application_route_id", "status", "current_stage", "current_message", "updated_at"])
            send_deployment_update(deployment.id, "deploying", deployment.current_message, deployment.status)
        else:
            # if github url
            if deployment.source_url:
                #print("iii33")
                Path(work_dir).mkdir(parents=True, exist_ok=True)
                deployment.status = Deployment.Status.BUILDING
                deployment.save(update_fields=["application_route_id", "status", "updated_at"])
                send_deployment_update(deployment.id, "cloning", "Cloning source repository", deployment.status)
                if run_command(deployment.id, ["git", "clone", "--depth", "1", deployment.source_url, work_dir]):
                    send_deployment_update(deployment.id, "failed", "git clone failed", deployment.status)
                    raise RuntimeError("git clone failed")

            #print("run_deploymenyt-111")
            send_deployment_update(deployment.id, "buildkit", "Starting BuildKit", deployment.status)
            deployment.status = Deployment.Status.BUILDING
            deployment.image_tag = image_tag
            deployment.save(update_fields=["application_route_id", "status", "image_tag", "updated_at"])
            railpack = os.environ.get("RAILPACK_BIN", "railpack")
            with docker_registry_environment() as build_env:
                ensure_buildkit(deployment.id, buildkit_name, environment=build_env)
                build_env["BUILDKIT_HOST"] = f"docker-container://{buildkit_name}"
                # Ensure mise does not fail when python artifact attestations are absent
                mise_toml_path = Path(work_dir) / "mise.toml"
                if mise_toml_path.exists():
                    mise_content = mise_toml_path.read_text(encoding="utf-8")
                    if "github_attestations" not in mise_content:
                        mise_content += "\n[settings]\npython.github_attestations = false\n"
                        mise_toml_path.write_text(mise_content, encoding="utf-8")
                else:
                    mise_toml_path.write_text("[settings]\npython.github_attestations = false\n", encoding="utf-8")

                send_deployment_update(deployment.id, "build", "Building image", deployment.status)
                write_railpack_config(work_dir)
                if run_command(
                    deployment.id,
                    [railpack, "build", "--name", image_tag, work_dir],
                    env=build_env,
                    timeout=25 * 60,
                ):
                    error_msg = "Railpack build failed"
                    send_deployment_update(deployment.id, "failed", error_msg, deployment.status)
                    raise RuntimeError(error_msg)

        #print("run_deploymenyt-222")
        deployment.container_name = container_name
        deployment.save(update_fields=["status", "container_name", "updated_at"])
        send_deployment_update(deployment.id, "container", "Starting container deployment", deployment.status)

        subprocess.run(
            ["docker", "rm", "-f", container_name],
            check=False,
            capture_output=True,
            timeout=30,
        )
        if run_command(deployment.id, ["docker", "run", "-d", "--name", container_name, "-e", "PORT=3000", "-p", "127.0.0.1::3000", image_tag]):
            error_msg = "docker run failed"
            send_deployment_update(deployment.id, "failed", error_msg, deployment.status)
            raise RuntimeError(error_msg)

        try:
            ensure_container_running(container_name)
            host_port = run_port(deployment.id, container_name)
            wait_for_readiness(
                deployment_id=deployment.id,
                container_name=container_name,
                host_port=host_port,
                timeout=120,
            )
            logs = subprocess.run(
                ["docker", "logs", container_name],
                capture_output=True,
                text=True,
                timeout=60,
            )
            log_line = f"[DEPLOYMENT {deployment.id}] CONTAINER LOGS:\n{logs.stdout}\n{logs.stderr}\n"
            send_deployment_log_chunk(deployment.id, log_line)
            queue_deployment_log_persist(deployment_id, log_line)
            print(f"[DEPLOYMENT {deployment.id}] CONTAINER LOGS: {log_line}", flush=True)
        except RuntimeError:
            logs = subprocess.run(
                ["docker", "logs", "--tail", "100", container_name],
                capture_output=True,
                text=True,
                timeout=60,
            )
            log_line = f"[DEPLOYMENT {deployment.id}] CONTAINER LOGS:\n{logs.stdout}\n{logs.stderr}\n"
            send_deployment_log_chunk(deployment.id, log_line)
            queue_deployment_log_persist(deployment_id, log_line)
            print(f"[DEPLOYMENT {deployment.id}] CONTAINER LOGS:\n{log_line}", flush=True)

            raise

        send_deployment_update(deployment.id, "routing", "Configuring application route", deployment.status)
        deployment.host_port = host_port
        deployment.save(update_fields=["host_port", "updated_at"])
        previous_active = list(
            Deployment.objects.filter(application_route_id=application_route_id, is_active=True)
            .exclude(pk=deployment.id)
        )
        configure_caddy(application_route_id, deployment.id, host_port)
        deployment.live_url = f"http://localhost:8080/apps/{application_route_id}/"
        deployment.status = Deployment.Status.RUNNING
        deployment.is_active = True 
        deployment.current_stage = "complete"
        deployment.current_message = f"Deployment is live at {deployment.live_url}"
        with transaction.atomic():
            Deployment.objects.filter(application_route_id=application_route_id, is_active=True).exclude(pk=deployment.id).update(
                is_active=False,
                status=Deployment.Status.SUPERSEDED,
                current_stage="superseded",
                current_message=f"Replaced by deployment #{deployment.id}",
                live_url=deployment.live_url,
            )
            Deployment.objects.filter(application_route_id=application_route_id).update(live_url=deployment.live_url)
            
            deployment.save(update_fields=["host_port", "live_url", "status", "is_active", "current_stage", "current_message", "updated_at"])
        send_deployment_update(deployment.id, "complete", f"Deployment is live at {deployment.live_url}", deployment.status)
        for old_deployment in previous_active:
            if not old_deployment.container_name:
                continue
            try:
                stop_result = subprocess.run(
                    ["docker", "stop", "--time", "10", old_deployment.container_name],
                    capture_output=True,
                    text=True,
                    timeout=20,
                )
                if stop_result.returncode == 0:
                    subprocess.run(
                        ["docker", "rm", old_deployment.container_name],
                        check=False,
                        capture_output=True,
                        text=True,
                        timeout=20,
                    )
            except (OSError, subprocess.TimeoutExpired) as stop_error:
                print(f"Could not stop superseded deployment {old_deployment.id}: {stop_error}", flush=True)
        
        #print("run_deploymenyt-333")

    except (
        OSError,
        subprocess.CalledProcessError,
        subprocess.TimeoutExpired,
        RuntimeError,
        Deployment.DoesNotExist,
        SoftTimeLimitExceeded,
    ) as error:
        print(f"[DEPLOYMENT {deployment.id}] ERROR: {error}", flush=True)
        cleanup_failed_deployment_container(deployment, error)
        if not isinstance(error, CaddyReloadError):
            deployment.host_port = None
        deployment.status = Deployment.Status.FAILED
        deployment.error = str(error)
        error_text = f"ERROR: {error}\n"
        deployment.current_stage = "failed"
        deployment.current_message = str(error)
        deployment.save(update_fields=["status", "host_port", "error", "current_stage", "current_message", "updated_at"])
        send_deployment_log_chunk(deployment.id, error_text)
        queue_deployment_log_persist(deployment.id, error_text)
        send_deployment_update(deployment.id, "failed", str(error), deployment.status)
    finally:
        close_old_connections()



