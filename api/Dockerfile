# Multi-stage Dockerfile for SeaweedFS Dashboard with Template Rendering
# Stage 1: Template Renderer
FROM python:3.9-slim

# Install dependencies for template rendering
RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

COPY api.py .

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start nginx
CMD ["python", "/app/api.py"]
