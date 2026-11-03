# Use NVIDIA's official PyTorch image with CUDA and NCCL pre-configured
FROM nvcr.io/nvidia/pytorch:24.03-py3

# Set working directory inside the container
WORKDIR /workspace/infrastructure

# Install required system dependencies and Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    iputils-ping \
    && rm -rf /var/lib/apt/lists/*

# Copy your infrastructure scripts and requirements into the container
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy infrastructure only. Model code/config/data are separate runtime mounts.
COPY . /workspace/infrastructure/

# Ensure execution permissions on shell scripts
RUN chmod +x *.sh

# Default entrypoint
CMD ["bash"]
