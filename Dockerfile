# Use the official Python image from the Docker Hub
FROM python:3.12-slim 

# Set environment variables
ENV POETRY_VERSION=1.8.5
ENV VIRTUAL_ENV=/opt/venv

# Install Poetry
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Create a virtual environment
RUN python -m venv $VIRTUAL_ENV
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Set the working directory in the container
WORKDIR /app

# Copy the poetry.lock and pyproject.toml files first to leverage Docker cache
COPY pyproject.toml poetry.lock* ./

# Install dependencies
RUN poetry install --only main --no-root

# Copy your Streamlit application (agent.py)
COPY src /app/src/

# Expose the Fastapi port (default: 8000)
EXPOSE 8000

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]