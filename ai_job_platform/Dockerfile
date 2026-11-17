# syntax=docker/dockerfile:1
FROM python:3.11-slim

# Prevent Python from writing .pyc files & enable unbuffered stdout
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install system dependencies, font configuration, and modern TeX fonts
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ca-certificates \
    fontconfig \
    libfontconfig1 \
    fonts-lmodern \
    fonts-texgyre \
    && rm -rf /var/lib/apt/lists/*

# Install Tectonic (fast standalone modern TeX engine)
RUN curl --proto '=https' --tlsv1.2 -fsSL https://drop-sh.tectonic-typesetting.net | sh \
    && mv tectonic /usr/local/bin/tectonic \
    && tectonic --version

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
