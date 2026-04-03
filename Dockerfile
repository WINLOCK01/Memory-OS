FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# We'll volume mount the code in dev, but for prod we copy:
COPY . .

# EXPOSE isn't strictly necessary for compose, but good practice
EXPOSE 8000
EXPOSE 8501
