FROM python:3.11-slim-bookworm

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        libffi-dev \
        musl-dev \
        ffmpeg \
        aria2 \
    && rm -rf /var/lib/apt/lists/*

# keep the rest of your original Dockerfile lines below this
# (WORKDIR, COPY, pip install, CMD, etc.)
