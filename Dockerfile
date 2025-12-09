FROM nvidia/cuda:12.1.0-base-ubuntu22.04
ENV DEBIAN_FRONTEND=noninteractive
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
RUN /app/.venv/bin/python -m pip install --upgrade pip

# ------------------------------------------
# Copy and install dependencies
# ------------------------------------------
COPY requirements.txt .
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ------------------------------------------
# Copy application folder
# ------------------------------------------
COPY app ./app

# ------------------------------------------
# Run the FastAPI app using uvicorn
# ------------------------------------------
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["/app/.venv/bin/uvicorn", "app.main:app"] FROM nvidia/cuda:12.1.0-base-ubuntu22.04

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
RUN /app/.venv/bin/python -m pip install --upgrade pip

# ------------------------------------------
# Copy and install dependencies
# ------------------------------------------
COPY requirements.txt .
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ------------------------------------------
# Copy application folder
# ------------------------------------------
COPY app ./app

# ------------------------------------------
# Run the FastAPI app using uvicorn
# ------------------------------------------
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
