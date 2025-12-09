FROM nvidia/cuda:12.1.0-base-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime
# ------------------------------------------
# Install Python 3.11 + system dependencies
# ------------------------------------------
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y python3.11 python3.11-venv python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

# CUDA compat (RunPod pattern)
RUN ldconfig /usr/local/cuda-12.1/compat/ || true

# ------------------------------------------
# Create working directory
# ------------------------------------------
WORKDIR /app

# ------------------------------------------
# Create virtual environment
# ------------------------------------------
RUN python3.11 -m venv /app/.venv
RUN /app/.venv/bin/python -m pip install --upgrade pip

# ------------------------------------------
# Copy and install dependencies
# ------------------------------------------
COPY requirements.txt .
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ------------------------------------------
# Copy application code
# ------------------------------------------
COPY app ./app

# ------------------------------------------
# Run the FastAPI app using Python entrypoint
# (this will start both PORT and PORT_HEALTH servers)
# ------------------------------------------
CMD ["/app/.venv/bin/python", "-m", "app.main"]
