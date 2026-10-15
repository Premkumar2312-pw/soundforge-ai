# Multi-stage Dockerfile for SoundForge AI
FROM python:3.11-slim as base

# Install system dependencies including libsndfile
RUN apt-get update && apt-get install -y --no-install-recommends \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Create non-root user
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -s /bin/bash -m appuser

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Set permissions for storage
RUN mkdir -p /app/storage && chown -R appuser:appgroup /app

USER appuser

ENV HOST=0.0.0.0
ENV PORT=8000
ENV PYTHONPATH=/app
ENV STORAGE_DIR=/app/storage
ENV DEFAULT_TARGET_LOUDNESS=-16.0
ENV DEFAULT_SAMPLE_RATE=48000

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

CMD ["uvicorn", "soundforge.api.app:app", "--host", "0.0.0.0", "--port", "8000"]
