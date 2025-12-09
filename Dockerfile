FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# Avoid tzdata interactive prompt
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Etc/UTC

# ------------------------------------------
# Install Python 3.11 + basic system deps
# ------------------------------------------
RUN apt-get update -y && \
    apt-get install -y --no-install-recommends \
        software-properties-common \
        tzdata \
        curl \
        ca-certificates \
        build-essential && \
    ln -fs /usr/share/zoneinfo/$TZ /etc/localtime && \
    dpkg-reconfigure -f noninteractive tzdata && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y --no-install-recommends \
        python3.11 \
        python3.11-venv \
        python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

# CUDA compat (RunPod pattern)
RUN ldconfig /usr/local/cuda-12.1/compat/ || true

# ------------------------------------------
# Workdir
# ------------------------------------------
WORKDIR /app

# ------------------------------------------
# Create venv & install deps
# ------------------------------------------
COPY requirements.txt .

RUN python3.11 -m venv /app/.venv && \
    /app/.venv/bin/python -m pip install --upgrade pip && \
    /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ------------------------------------------
# Copy app code
# ------------------------------------------
COPY app ./app

# Optional but nice
EXPOSE 8000

# ------------------------------------------
# Start FastAPI via uvicorn
# ------------------------------------------
# Make sure main.py contains: app = FastAPI()
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
