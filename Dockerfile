FROM python:3.11-slim

WORKDIR /app

# Reduce size + avoid extra filesW
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PIP_NO_CACHE_DIR=1
ENV PIP_DISABLE_PIP_VERSION_CHECK=1

# (Optional but helpful) some libs (like scipy) sometimes need system deps.
# If you don't need scipy, remove it from requirements instead.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# DigitalOcean App Platform usually routes traffic to $PORT
EXPOSE 8080
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
