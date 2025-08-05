# Multi-stage build for Railway deployment
FROM python:3.11-slim as builder

# Set environment for non-interactive builds
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    cmake \
    build-essential \
    wget \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Build whisper.cpp
WORKDIR /build
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git && \
    cd whisper.cpp && \
    make -j2 && \
    ls -la . && \
    # Check if build directory exists, if not create it
    test -d build/bin || (echo "Creating build/bin directory" && mkdir -p build/bin && cp main build/bin/whisper-cli) && \
    # Verify binary exists
    test -f build/bin/whisper-cli || test -f main && \
    # If whisper-cli doesn't exist but main does, copy it
    (test -f build/bin/whisper-cli || cp main build/bin/whisper-cli) && \
    # Download model
    bash ./models/download-ggml-model.sh small

# Production stage
FROM python:3.11-slim

# Environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8080

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Create directories
RUN mkdir -p whisper.cpp/build/bin whisper.cpp/models

# Copy whisper binary (try both possible locations)
COPY --from=builder /build/whisper.cpp/build/bin/whisper-cli ./whisper.cpp/build/bin/whisper-cli
COPY --from=builder /build/whisper.cpp/models/ggml-small.bin ./whisper.cpp/models/

# Set permissions
RUN chmod +x ./whisper.cpp/build/bin/whisper-cli

# Copy app
COPY main.py .

# Create transcript file
RUN touch transcript.txt

# Expose port
EXPOSE $PORT

# Run app
CMD ["python", "main.py"] 