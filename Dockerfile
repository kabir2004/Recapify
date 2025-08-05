# Use multi-stage build for efficiency
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    git \
    cmake \
    build-essential \
    wget \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Build whisper.cpp in builder stage
WORKDIR /build
RUN git clone --depth 1 https://github.com/ggerganov/whisper.cpp.git && \
    cd whisper.cpp && \
    make -j$(nproc) && \
    # Download small model only
    ./models/download-ggml-model.sh small

# Final stage
FROM python:3.11-slim

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy whisper.cpp binaries and models from builder
COPY --from=builder /build/whisper.cpp/build/bin/whisper-cli ./whisper.cpp/build/bin/whisper-cli
COPY --from=builder /build/whisper.cpp/models/ggml-small.bin ./whisper.cpp/models/ggml-small.bin

# Make whisper-cli executable
RUN chmod +x ./whisper.cpp/build/bin/whisper-cli

# Copy application code
COPY main.py .

# Create necessary directories and files
RUN mkdir -p whisper.cpp/models && \
    touch transcript.txt

# Set environment variables for Railway
ENV PYTHONUNBUFFERED=1
ENV PORT=7860

# Expose port (Railway will override this)
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT:-7860}/ || exit 1

# Run the app
CMD ["python", "main.py"] 