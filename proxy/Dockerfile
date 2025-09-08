# Multi-stage Dockerfile for SeaweedFS Dashboard with Template Rendering
# Stage 1: Template Renderer
FROM python:3.9-slim AS template-renderer

# Install dependencies for template rendering
RUN apt-get update && apt-get install -y \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy template generation files
COPY generate_templates.py requirements.txt ./
COPY templates/ ./templates/

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Render templates during build
RUN python3 generate_templates.py

# Stage 2: Final Nginx Image
FROM nginx:alpine

# Copy rendered HTML files from template renderer stage
COPY --from=template-renderer /app/html/ /etc/nginx/html/

# Copy the main dashboard file
COPY cluster.html /etc/nginx/html/

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose ports
EXPOSE 80 9333

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost/ || exit 1

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
