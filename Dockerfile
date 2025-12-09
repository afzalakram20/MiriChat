FROM nvidia/cuda:12.1.0-base-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive

# -----------------------------
# Install Python 3.11
# -----------------------------
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y python3.11 python3.11-venv python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

RUN ldconfig /usr/local/cuda-12.1/compat/ || true

# -----------------------------
# Workdir
# -----------------------------
WORKDIR /app

# -----------------------------
# Virtualenv
# -----------------------------
RUN python3.11 -m venv /app/.venv
RUN /app/.venv/bin/python -m pip install --upgrade pip

# -----------------------------
# Install Python deps
# -----------------------------
COPY requirements.txt .
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# -----------------------------
# Copy application code
# -----------------------------
COPY app ./app
COPY runpod_entry.py ./runpod_entry.py

# -----------------------------
# Start FastAPI via RunPod entry
# -----------------------------
CMD ["/app/.venv/bin/python", "runpod_entry.py"]
