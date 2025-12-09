FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# ------------------------------------------
# Install Python 3.11 + system dependencies
# ------------------------------------------
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y python3.11 python3.11-venv python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

RUN ldconfig /usr/local/cuda-12.1/compat/ || true

# ------------------------------------------
# Create working directory
# ------------------------------------------
WORKDIR /app

# ------------------------------------------
# Create virtual environment
# ------------------------------------------
RUN python3.11 -m venv /app/.venv

# Activate venv & upgrade pip
RUN /app/.venv/bin/python -m pip install --upgrade pip

# ------------------------------------------
# Install dependencies inside venv
# ------------------------------------------
COPY requirements.txt .
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ------------------------------------------
# Copy FastAPI app
# ------------------------------------------
COPY app.py .

# ------------------------------------------
# Run app using venv Python
# ------------------------------------------
CMD ["/app/.venv/bin/python", "app.py"]
