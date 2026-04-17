import json
from pyexpat import model

from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers import Taskapi 
from rest_framework.response import Response
from rest_framework import status, generics
from .models import Tasks
from django.db.models import Q
from django.db.models import F, Max
import time
from google import genai
from django.conf import settings
import requests
from google.genai import errors





# Create your views here.

class CreateTask(APIView):
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        highest_number = Tasks.objects.aggregate(max_tasks=Max('tasks_number'))
        if highest_number["max_tasks"] is None:
            highest_number = 1
        else:
            highest_number = highest_number["max_tasks"] + 1

        mutable_querydict = request.data.copy()
        print('mutable_querydict')
        print(mutable_querydict)

        # Convert the 'expires' field to a datetime string in the required format
        expires = mutable_querydict.get('expires', None)
        if expires:
            try:
                expires_datetime = datetime.strptime(expires, '%Y-%m-%d')  # Parse the date
                mutable_querydict['expires'] = expires_datetime.isoformat()  # Convert to ISO format
            except ValueError as e:
                return Response(
                    {"expires": "Invalid date format. Please use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        mutable_querydict["tasks_number"] = highest_number

        serializer = Taskapi(data=mutable_querydict, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            formatted_errors = {field: ", ".join(errors) for field, errors in serializer.errors.items()}
            return Response(formatted_errors, status=status.HTTP_400_BAD_REQUEST)

class TaskQuerysetMixin:
    def get_queryset(self):
        return Tasks.objects.all()


class ListTasks(TaskQuerysetMixin, generics.ListAPIView):
    serializer_class= Taskapi


class TaskDeleteView(TaskQuerysetMixin, generics.DestroyAPIView):
    serializer_class = Taskapi

    def delete(self, request, *args, **kwargs):
        name = self.kwargs.get('name')
        try:
            instance = self.get_queryset().get(name=name)
            deleted_number = instance.tasks_number
            self.perform_destroy(instance)
            remaining_books = Tasks.objects.filter(tasks_number__gt=deleted_number)
            remaining_books.update(tasks_number=F('tasks_number') - 1)

            return Response(status=status.HTTP_204_NO_CONTENT)
        except Tasks.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        


class TaskUpdateView(TaskQuerysetMixin, generics.UpdateAPIView):
    serializer_class = Taskapi
    parser_classes = [MultiPartParser] 

    def update(self, request, *args, **kwargs):
        name = self.kwargs.get('name')  # Get the 'pk' captured from URL
        try:
            instance = self.get_queryset().get(name=name)
            mutable_querydict = request.data.copy()
            expires = mutable_querydict.get('expires', None)
            if expires:
                expires_datetime = datetime.strptime(expires, '%Y-%m-%d')  # Parse the date
                mutable_querydict['expires'] = expires_datetime.isoformat()  # Convert to ISO format
            else:
                return Response(
                    {"expires": "Invalid date format. Please use YYYY-MM-DD."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            serializer = self.get_serializer(instance, data=mutable_querydict, partial=True, context={'request':request})
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
                # serializer.is_valid(raise_exception=True)
                # serializer.save()
                # return Response(serializer.data)
            else:
                formatted_errors = {field: ", ".join(errors) for field, errors in serializer.errors.items()}
            return Response(formatted_errors, status=status.HTTP_400_BAD_REQUEST)

        except Tasks.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)


class TaskSearchView(TaskQuerysetMixin,generics.ListAPIView):
    serializer_class = Taskapi

    def get_queryset(self):
        queryset = super().get_queryset()
        search_param = self.request.query_params.get('q', None)        

        if search_param:
                name_filter = Q(name__icontains=search_param)
                status_filter = Q(status__icontains=search_param)
                contributors_filter = Q(contributors__icontains=search_param)

                tasks_number_filter = Q()
                try:
                    search_param_as_number = int(search_param)
                    tasks_number_filter = Q(tasks_number=search_param_as_number)
                except ValueError:
                    pass 

                queryset = queryset.filter(
                    name_filter | status_filter | contributors_filter | tasks_number_filter
                )

            
        return queryset 


class TaskFinish(TaskQuerysetMixin, generics.UpdateAPIView):
    serializer_class = Taskapi

    def update(self, request, *args, **kwargs):
        name = self.kwargs.get('name')  # Get the 'pk' captured from URL
        try:
            instance = self.get_queryset().get(name=name)
            serializer = self.serializer_class(instance)
            if instance.status == "Started":
                instance.status = "Finished"
                instance.save(update_fields=["status"]) 
                return Response(serializer.data, status=status.HTTP_200_OK)
            else:
                return Response({"error": "Task is not in 'Started' status, It cannot be finished"},status=status.HTTP_400_BAD_REQUEST)
        except Tasks.DoesNotExist:
            return Response({"error": "Task not found."},status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({"error": str(e)},
                            status=status.HTTP_400_BAD_REQUEST)


def build_prompt(user_message, tasks):
    task_list = "\n".join([t.title for t in tasks])

    return f"""
    You are a productivity assistant.

    Here are the user's tasks:
    {task_list}

    User request:
    {user_message}

    Respond helpfully.
    """


def call_gemini(prompt):
    response = requests.post(
        "https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent",
        params={"API_KEY": settings.GEMINI_API_KEY},
        json={
            "contents": [
                {
                    "parts": [{"text": prompt}]
                }
            ]
        }
    )

    data = response.json()

    return data["candidates"][0]["content"]["parts"][0]["text"]



class AITaskActionView(APIView):
    def post(self, request):
        task_title = request.data.get("task")
        deadline = request.data.get("deadline")
        print("oboy", task_title, deadline)
        client = genai.Client(api_key=settings.GEMINI_API_KEY)

        prompt = f"""
        You are an AI assistant inside a task manager.

        Your job is to analyze a task and return structured output.

        Task:
        "{task_title}"
<<<<<<< HEAD
=======
        Deadline: "{deadline}"
>>>>>>> e37d7acd8c1297adb7a0fe3dc65428326a8c80df

        Do the following:
        1. Summarize the task in one short sentence
        2. Improve the task to make it clear and actionable
        3. Break the task into small actionable subtasks

        Return ONLY valid JSON in this format:

        {{
        "summary": "short summary",
        "improved": "clear and actionable version",
        "subtasks": [
            "step 1",
            "step 2",
            "step 3"
        ]
        }}

        Rules:
<<<<<<< HEAD
        - Do not include any explanation
=======
>>>>>>> e37d7acd8c1297adb7a0fe3dc65428326a8c80df
        - Do not include extra text outside JSON
        - Keep responses concise
        - Be friendly and encouraging
        - Explain concepts simply
        - Address the user by their name when possible
        - Do not go beyond giving advice related to task management and productivity
        """

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=prompt
                )
                raw = response.text
                clean = raw.replace("```json", "").replace("```", "").strip()
                data = json.loads(clean)
                print(response.text, data, "heyyy")

                return Response({"data": data})
            except errors.ClientError as e:
                # Handle quota / rate limit
                if "RESOURCE_EXHAUSTED" in str(e):
                    return Response(
                        {"error": "AI limit reached. Please wait a moment."},
                        status=429
                    )

                return Response(
                    {"error": "AI client error", "details": str(e)},
                    status=500
                )

            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid AI response format"},
                    status=500
                )

            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                    continue

                return Response(
                    {"error": "Unexpected error", "details": str(e)},
                    status=500
                )



class AIChatView(APIView):
    def post(self, request):
        client = genai.Client(api_key=settings.GEMINI_API_KEY)
        message = request.data.get("message")
        print("helo", message)
        prompt = f"""
<<<<<<< HEAD
        You are Zugo, a helpful assistant in a task manager app.
=======
        You are Nuel, a helpful assistant in a task manager app.
>>>>>>> e37d7acd8c1297adb7a0fe3dc65428326a8c80df

        Rules:
        - Be friendly and encouraging
        - Explain concepts simply
        - Address the user by their name when possible
        - Do not go beyond giving advice related to task management and productivity

        User: {message}
        """

        for attempt in range(3):
            try:
                response = client.models.generate_content(
                    model='gemini-2.5-flash', 
                    contents=prompt
                )
                print(response.text, response, "heyyy")

                return Response({"reply": response.text})
            except errors.ClientError as e:
                # Handle quota / rate limit
                if "RESOURCE_EXHAUSTED" in str(e):
                    return Response(
                        {"error": "AI limit reached. Please wait a moment."},
                        status=429
                    )

                return Response(
                    {"error": "AI client error", "details": str(e)},
                    status=500
                )

            except json.JSONDecodeError:
                return Response(
                    {"error": "Invalid AI response format"},
                    status=500
                )

            except Exception as e:
                if attempt < 2:
                    time.sleep(2)
                    continue

                return Response(
                    {"error": "Unexpected error", "details": str(e)},
                    status=500
                )
        