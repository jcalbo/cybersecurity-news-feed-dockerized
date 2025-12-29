# Backend Dockerfile - Cybersecurity News API
FROM python:3.12-slim

# Install uv - Fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY *.py ./

# Expose port
EXPOSE 8000

# Health check (using curl - simpler and more reliable)
RUN apt-get update && apt-get install -y --no-install-recommends curl && rm -rf /var/lib/apt/lists/*
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run the REST API server
CMD ["uv", "run", "python", "server_with_rest.py"]

