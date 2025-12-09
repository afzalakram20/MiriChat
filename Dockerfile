FROM nvidia/cuda:12.1.0-base-ubuntu22.04

# ------------------------------------------
# Prevent tzdata from blocking the build
# ------------------------------------------
ENV DEBIAN_FRONTEND=noninteractive
RUN ln -fs /usr/share/zoneinfo/Etc/UTC /etc/localtime

# ------------------------------------------
# Install Python 3.11
# ------------------------------------------
RUN apt-get update -y && \
    apt-get install -y software-properties-common && \
    add-apt-repository ppa:deadsnakes/ppa -y && \
    apt-get update -y && \
    apt-get install -y python3.11 python3.11-venv python3.11-distutils && \
    rm -rf /var/lib/apt/lists/*

RUN ldconfig /usr/local/cuda-12.1/compat/ || true

# ------------------------------------------
# Workdir
# ------------------------------------------
WORKDIR /app

# ------------------------------------------
# Create virtual environment
# ------------------------------------------
RUN python3.11 -m venv /app/.venv
RUN /app/.venv/bin/python -m pip install --upgrade pip

# ------------------------------------------
# Install dependencies
# ------------------------------------------
COPY requirements.txt .
RUN /app/.venv/bin/pip install --no-cache-dir -r requirements.txt

# ------------------------------------------
# Copy FastAPI application
# ------------------------------------------
COPY app ./app

# ------------------------------------------
# Start FastAPI from inside venv
# ------------------------------------------
CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
