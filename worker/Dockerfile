# Use the official Python image from the Docker Hub
FROM whisper_timestamped:latest as whisper_builder
FROM python:3.9-slim

# Set the working directory in the container
WORKDIR /app

# Install ffmpeg
RUN apt-get update && apt-get install -y \
    ffmpeg \
    build-essential \
    libssl-dev \
    libffi-dev \
    python3-dev \
    && apt-get clean

# Copy the current directory contents into the container at /app
COPY . /app

RUN ls -la /app

# Install any needed packages specified in requirements.txt
RUN python3 -m pip install -r requirements.txt

# Run video_processing.py when the container launches
CMD ["python", "app.py"]