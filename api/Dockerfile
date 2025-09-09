FROM python:3.9-slim

ARG DOCKER_GID=999

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc curl \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api.py .

# Create docker group and add user to it
RUN groupadd -r -g ${DOCKER_GID} docker && \
    useradd --create-home --shell /bin/bash --groups docker app && \
    chown -R app:app /app

USER app

EXPOSE 8080

CMD ["python", "api.py"]
