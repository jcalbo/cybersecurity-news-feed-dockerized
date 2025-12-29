# Backend Dockerfile - Cybersecurity News API
FROM python:3.12-slim

# Install uv - Fast Python package installer
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install dependencies with uv
RUN uv sync --frozen --no-dev

# Copy application code
COPY *.py ./

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1

# Run the REST API server
CMD ["uv", "run", "python", "server_with_rest.py"]

