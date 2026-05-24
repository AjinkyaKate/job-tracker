# Job Tracker — production image for Fly.io
# Single-stage build: Python 3.11 slim + uvicorn binding to Fly's $PORT.

FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install deps first so source edits don't bust the layer cache.
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy only what the app needs at runtime.
COPY webapp.py tracker.py gmail_integration.py ./
COPY templates/ ./templates/

# Fly.io sets $PORT (defaults to 8080). The internal_port in fly.toml must match.
EXPOSE 8080

# Use shell form so $PORT is expanded at runtime, not at image-build time.
CMD ["sh", "-c", "uvicorn webapp:app --host 0.0.0.0 --port ${PORT:-8080}"]
