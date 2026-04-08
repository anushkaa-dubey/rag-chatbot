# RAG Legal Assistant — Docker Image
# Base: slim Python 3.11 for smaller image size
FROM python:3.11-slim

# Metadata
LABEL maintainer="Anushkaa Dubey"
LABEL description="RAG Legal Assistant — FastAPI Backend"

# Environment
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# System dependencies (PDF processing needs libmagic)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libmagic1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies first (layer cache optimization)
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source
COPY app/ ./app/
COPY run_api.py .
COPY .env .

# Create necessary directories
RUN mkdir -p pdfs vectorstore logs

# Expose API port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/api/v1/health')"

# Run API server
CMD ["python", "run_api.py"]
