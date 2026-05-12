# FROM python:3.12-slim

# WORKDIR /app
# COPY backend/requirements.txt .
# RUN apt-get update && apt-get install -y \
#     gcc \
#     python3-dev \
#     libffi-dev \
#     zlib1g-dev \
#     libjpeg-dev \
#     && rm -rf /var/lib/apt/lists/*
# RUN pip install --default-timeout=1000 -r requirements.txt
# COPY . .
# EXPOSE 8000
# CMD ["python", "backend/manage.py", "runserver", "0.0.0.0:8000"]


# Stage 1: build dependencies
FROM python:3.12-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc \
    python3-dev \
    libffi-dev \
    zlib1g-dev \
    libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*
    
COPY backend/requirements.txt .
RUN pip install --user -r requirements.txt

# Stage 2: final image (clean)
FROM python:3.12-slim

WORKDIR /app

# Copy installed packages only
COPY --from=builder /root/.local /root/.local

COPY backend/ .

ENV PATH=/root/.local/bin:$PATH

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]