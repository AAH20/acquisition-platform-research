# Multi-stage build for acquisition-platform
# Stage 1: Builder
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy project files
COPY pyproject.toml README.md ./
COPY src/ src/

# Install package
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime
FROM python:3.12-slim AS runtime

WORKDIR /app

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Set ownership
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Default command
CMD ["python", "-c", "import acquisition_platform; print(acquisition_platform.__version__)"]
