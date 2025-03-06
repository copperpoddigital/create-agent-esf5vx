# Build stage
FROM python:3.10-slim AS builder

# Set environment variables for Python and Poetry
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    POETRY_VERSION=1.5.1 \
    POETRY_NO_INTERACTION=1 \
    POETRY_VIRTUALENVS_CREATE=false

# Set working directory for the container
WORKDIR /app

# Install system dependencies required for building Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install Poetry for dependency management
RUN pip install --no-cache-dir "poetry==$POETRY_VERSION"

# Copy Poetry configuration files
COPY pyproject.toml poetry.lock* ./

# Install production dependencies
RUN poetry install --no-dev --no-root

# Copy application source code
COPY . .

# Create directories for document storage and vector indices
RUN mkdir -p /app/data/documents /app/data/vector_indices

# Final stage with a clean base image
FROM python:3.10-slim AS final

# Set Python environment variables in the final image
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Set working directory for the final container
WORKDIR /app

# Install minimal runtime dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    libpq5 && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user and group for running the application
RUN groupadd -r appgroup && \
    useradd -r -g appgroup appuser

# Create data directories and set appropriate permissions
RUN mkdir -p /app/data/documents /app/data/vector_indices && \
    chown -R appuser:appgroup /app

# Copy installed dependencies from builder stage
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages

# Copy application code from builder stage
COPY --from=builder /app /app

# Ensure all files are owned by the non-root user
RUN chown -R appuser:appgroup /app

# Switch to non-root user for running the application
USER appuser

# Expose the port the application will run on
EXPOSE 8000

# Define the command to run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]