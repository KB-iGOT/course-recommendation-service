FROM python:3.12-slim

# Create appuser (both user and group)
RUN groupadd -g 1001 appuser \
    && useradd -u 1001 -g appuser -m appuser

ENV POETRY_VERSION=1.8.5
ENV VIRTUAL_ENV=/opt/venv

# Install poetry + build tools
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
    && pip install --no-cache-dir "poetry==$POETRY_VERSION" \
    && rm -rf /var/lib/apt/lists/*

# Create a virtual environment
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml poetry.lock* ./

# Install deps
RUN poetry install --only main --no-root

# Copy application
COPY src /app/src/

# Fix permissions so appuser can access everything
RUN chown -R appuser:appuser /app /opt/venv

# Switch to non-root user
USER appuser

EXPOSE 8000

# Start FastAPI
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
