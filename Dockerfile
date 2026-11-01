# ==============================================================================
# Production Dockerfile for Real-Time UPI Fraud Detection System
# Multi-stage lightweight Python runtime with model artifacts and healthcheck
# ==============================================================================

FROM python:3.11-slim

# Prevent Python from writing .pyc files and enable unbuffered logging
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Install curl for healthcheck probe
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# 1. Install dependencies first to leverage Docker layer caching
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 2. Copy application source code, artifacts, and frontend assets
COPY . .

# 3. Expose service port
EXPOSE 8000

# 4. Container Healthcheck (polls /health endpoint every 30s)
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# 5. Start Uvicorn ASGI server
CMD ["uvicorn", "api.index:app", "--host", "0.0.0.0", "--port", "8000"]
