# Use the official Python image from Docker Hub
FROM python:3.12-slim

# Create non-root user and group
RUN groupadd -r appgroup && useradd -r -g appgroup appuser

# Environment variables
ENV POETRY_VERSION=1.8.5
ENV VIRTUAL_ENV=/opt/venv

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Create virtual environment
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Create working directory and set permissions
WORKDIR /app
RUN mkdir -p /app && chown
