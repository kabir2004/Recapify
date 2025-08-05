FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY . .

# Build whisper.cpp efficiently
RUN git clone https://github.com/ggerganov/whisper.cpp.git && \
    cd whisper.cpp && \
    make && \
    ./models/download-ggml-model.sh small && \
    cd .. && \
    # Clean up build artifacts to reduce image size
    rm -rf whisper.cpp/.git whisper.cpp/examples whisper.cpp/tests

# Create necessary directories
RUN mkdir -p whisper.cpp/models

# Expose port
EXPOSE 7860

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV GRADIO_SERVER_PORT=7860
ENV GRADIO_SERVER_NAME=0.0.0.0

# Run the app
CMD ["python", "main.py"] 