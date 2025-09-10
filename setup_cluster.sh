#!/bin/bash

# Script to set up and start the SeaweedFS HA cluster with basic authentication
# 
# Usage: 
#   ./setup_cluster.sh [username] [password] [domain]
# 
# Parameters:
#   username - Admin username for cluster management (default: admin)
#   password - Admin password for cluster management (default: seaweedadmin)
#   domain   - Domain name for the cluster (default: example.com)
#
# This script:
#   1. Creates authentication credentials for the admin interface
#   2. Generates S3 API credentials
#   3. Creates a .env file with all configuration
#   4. Builds the Docker images
#   5. Starts the SeaweedFS HA cluster with 3 masters, 3 volumes, and 2 filers

# Default values
DEFAULT_USERNAME="admin"
DEFAULT_PASSWORD="seaweedadmin"
DEFAULT_DOMAIN="example.com"

# Generate random S3 credentials if needed
RANDOM_ACCESS_KEY=$(openssl rand -hex 20)
RANDOM_SECRET_KEY=$(openssl rand -hex 40)

# Use provided credentials or defaults
USERNAME=${1:-$DEFAULT_USERNAME}
PASSWORD=${2:-$DEFAULT_PASSWORD}
DOMAIN=${3:-$DEFAULT_DOMAIN}

echo "Setting up SeaweedFS HA cluster..."

# Check if docker is available
if ! command -v docker &> /dev/null; then
    echo "docker not found. Please install Docker first."
    exit 1
fi

# Check if docker compose is available
if ! docker compose version &> /dev/null; then
    echo "docker compose not found. Please install Docker Compose v2."
    exit 1
fi

# Docker GID for API container socket access
DOCKER_GID=$(getent group docker | cut -d: -f3)
if [ -z "$DOCKER_GID" ]; then
    echo "Warning: Could not determine docker group GID. Using default 999."
    DOCKER_GID=999
fi

# Check if htpasswd utility is available
if ! command -v htpasswd &> /dev/null; then
    echo "htpasswd utility not found. Attempting to install apache2-utils..."
    if command -v apt-get &> /dev/null; then
        sudo apt-get update -y
        sudo apt-get install -y apache2-utils
    elif command -v yum &> /dev/null; then
        sudo yum install -y httpd-tools
    else
        echo "Error: Could not install apache2-utils automatically."
        echo "Please install the package that provides 'htpasswd' for your distribution."
        exit 1
    fi
fi

# Create .htpasswd file
echo "Creating .htpasswd file with username: $USERNAME"
htpasswd -bc .htpasswd "$USERNAME" "$PASSWORD"

# Create .env file with necessary environment variables
echo "Creating .env file with domain: $DOMAIN"
cat > .env << EOL
# SeaweedFS environment configuration
# Generated on $(date)

# Domain configuration
DOMAIN=${DOMAIN}

# Docker group ID for API container socket access
DOCKER_GID=${DOCKER_GID}

# SeaweedFS URL endpoints (through nginx proxy)
SEAWEED_MASTER_URL=http://localhost/master/1
SEAWEED_VOLUME_URL=http://localhost/volume/1
SEAWEED_FILER_URL=http://localhost:8080
SEAWEED_S3_URL=http://localhost:9333

# Authentication for admin access
SEAWEED_AUTH_USER=${USERNAME}
SEAWEED_AUTH_PASSWORD=${PASSWORD}

# S3 API credentials
AWS_ACCESS_KEY_ID=${RANDOM_ACCESS_KEY}
AWS_SECRET_ACCESS_KEY=${RANDOM_SECRET_KEY}
EOL

# Build the Docker images
echo "Building Docker images..."
if ! docker compose build; then
    echo "Error: Failed to build Docker images."
    echo "Check the build output above for details."
    exit 1
fi

# Start the cluster
echo "Starting SeaweedFS HA cluster..."
if ! docker compose up -d; then
    echo "Error: Failed to start SeaweedFS HA cluster."
    echo "Check the docker compose output above for details."
    exit 1
fi

echo "Waiting for services to start..."
echo "This may take a moment as containers initialize..."
sleep 15

# Check container status
echo "Container Status:"
docker compose ps

echo "======================================================================================"
echo "🌟 SeaweedFS HA cluster is now running! 🌟"
echo "======================================================================================"
echo ""
echo "📂 Local Access:"
echo "--------------------------------------"
echo "- Dashboard:     http://localhost/"
echo "- Master 1:      http://localhost/master/1/"
echo "- Volume 1:      http://localhost/volume/1/"
echo "- Filer 1:       http://localhost/filer/1/"
echo "- API Docs:      http://localhost/api/docs"
echo ""
echo "🔗 Filer:"
echo "- Filer:         http://localhost:8080/"
echo ""
echo "🔗 S3 API:"
echo "--------------------------------------"
echo "- S3 API:        http://localhost:9333/"
echo ""
echo "🔐 Admin Authentication:"
echo "--------------------------------------"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo ""
echo "🔑 S3 API Credentials:"
echo "--------------------------------------"
echo "Access Key: $RANDOM_ACCESS_KEY"
echo "Secret Key: $RANDOM_SECRET_KEY"
echo ""
echo "📝 Environment Configuration:"
echo "--------------------------------------"
echo "All configuration has been saved to .env file"
echo "Docker GID set to: $DOCKER_GID"
echo ""
echo "======================================================================================"
echo "✅ Setup complete! Access the dashboard at: http://localhost/"
echo "======================================================================================"