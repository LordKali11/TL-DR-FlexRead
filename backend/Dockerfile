# NZZ FlexRead Backend - Google Cloud Run Dockerfile
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    PYTHONPATH=/app

WORKDIR /app

# Install system dependencies if required
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend source code and sample input data
COPY backend /app/backend
COPY input /app/input

EXPOSE 8080

CMD exec uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT}
