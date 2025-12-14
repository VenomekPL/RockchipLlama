# Dockerfile for RockchipLlama (RK3588)
# Based on Ubuntu 22.04 for ARM64

# Stage 1: Builder
FROM ubuntu:22.04 AS builder

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install build dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-venv \
    git \
    wget \
    gcc \
    g++ \
    make \
    cmake \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2: Runtime
FROM ubuntu:22.04

# Prevent interactive prompts
ENV DEBIAN_FRONTEND=noninteractive

# Install runtime dependencies
# librkllmrt.so requires libgomp1
RUN apt-get update && apt-get install -y \
    python3 \
    python3-venv \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy application code
COPY . .

# Copy RKLLM runtime library (Assuming it's in external/rknn-llm/rkllm-runtime/Linux/librkllm_api/aarch64/)
# NOTE: You must ensure the submodule is initialized and updated before building!
# If not, you might need to download it or mount it.
# For now, we assume the user has the repo with submodules.
# We need to move the library to /usr/lib/ or set LD_LIBRARY_PATH
# The path in the repo is: external/rknn-llm/rkllm-runtime/Linux/librkllm_api/aarch64/librkllmrt.so
COPY external/rknn-llm/rkllm-runtime/Linux/librkllm_api/aarch64/librkllmrt.so /usr/lib/librkllmrt.so

# Expose port
EXPOSE 8080

# Set environment variables
ENV PYTHONPATH=/app/src
ENV LD_LIBRARY_PATH=/usr/lib:$LD_LIBRARY_PATH

# Start server
CMD ["python3", "src/main.py"]
