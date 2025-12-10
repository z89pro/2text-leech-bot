# old (broken)
# FROM python:3.9.7-slim-buster

# new (working)
FROM python:3.9-slim-bullseye
# or even better (more up to date):
# FROM python:3.11-slim-bookworm

RUN apt-get update -y && apt-get upgrade -y \
    && apt-get install -y --no-install-recommends gcc libffi-dev musl-dev ffmpeg aria2 python3-pip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*
