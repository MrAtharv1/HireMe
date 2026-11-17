# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing .pyc files & enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies, essential fonts, and network tools
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fontconfig \
    fonts-lmodern \
    fonts-texgyre \
    tar \
    gzip \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic: Download official standalone statically-linked musl binary
# (Fully static with ZERO dynamic library dependencies, works seamlessly on x86_64 and aarch64)
RUN ARCH=$(uname -m) \
    && curl -fsSL "https://github.com/tectonic-typesetting/tectonic/releases/download/tectonic%400.15.0/tectonic-0.15.0-${ARCH}-unknown-linux-musl.tar.gz" -o tectonic.tar.gz \
    && tar -xzf tectonic.tar.gz -C /usr/local/bin \
    && rm tectonic.tar.gz \
    && chmod +x /usr/local/bin/tectonic \
    && /usr/local/bin/tectonic --version

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy source code and assets
COPY . .

# Create storage directories
RUN mkdir -p uploads generated storage/resumes

EXPOSE 8000

# Start FastAPI application with uvicorn
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
