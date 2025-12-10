FROM python:3.11-slim-bookworm

# Install required system deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        musl-dev \
        ffmpeg \
        aria2 \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy bot files
COPY . /app

# Install Python requirements
RUN pip install --no-cache-dir -r requirements.txt

# Start bot
CMD ["python3", "main.py"]
