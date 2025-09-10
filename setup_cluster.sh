#!/bin/bash

# Script to set up and start the SeaweedFS HA cluster with basic authentication
# 
# Usage: 
#   ./setup_cluster.sh [OPTIONS]
# 
# Options:
#   -u USERNAME              Admin username for cluster management (default: admin)
#   -p PASSWORD              Admin password for cluster management (default: seaweedadmin)
#   -d DOMAIN                Domain name for the cluster (default: example.com)
#   -i IP_ADDRESS            IP address for server access (default: localhost)
#   -a AWS_ACCESS_KEY_ID     AWS access key ID (default: generated)
#   -s AWS_SECRET_ACCESS_KEY AWS secret access key (default: generated)
#   -r AWS_REGION            AWS region (default: us-east-1)
#   -v AWS_S3_SIGNATURE_VERSION S3 signature version (default: s3v4)
#   -t AWS_S3_ADDRESSING_STYLE S3 addressing style (default: path)
#   -h                       Show this help message

# Default values
DEFAULT_USERNAME="admin"
DEFAULT_PASSWORD="seaweedadmin"
DEFAULT_DOMAIN="example.com"
DEFAULT_IP="localhost"
RANDOM_ACCESS_KEY=$(openssl rand -hex 20)
RANDOM_SECRET_KEY=$(openssl rand -hex 40)
DEFAULT_AWS_REGION="us-east-1"
DEFAULT_AWS_S3_SIGNATURE_VERSION="s3v4"
DEFAULT_AWS_S3_ADDRESSING_STYLE="path"

# Use provided credentials or defaults
USERNAME="$DEFAULT_USERNAME"
PASSWORD="$DEFAULT_PASSWORD"
DOMAIN="$DEFAULT_DOMAIN"
IP="$DEFAULT_IP"
AWS_ACCESS_KEY_ID="$RANDOM_ACCESS_KEY"
AWS_SECRET_ACCESS_KEY="$RANDOM_SECRET_KEY"
AWS_REGION="$DEFAULT_AWS_REGION"
AWS_S3_SIGNATURE_VERSION="$DEFAULT_AWS_S3_SIGNATURE_VERSION"
AWS_S3_ADDRESSING_STYLE="$DEFAULT_AWS_S3_ADDRESSING_STYLE"

# Function to display usage
usage() {
    echo "Usage: $0 [OPTIONS]"
    echo
    echo "Options:"
    echo "  -u USERNAME              Admin username for cluster management (default: admin)"
    echo "  -p PASSWORD              Admin password for cluster management (default: seaweedadmin)"
    echo "  -d DOMAIN                Domain name for the cluster (default: example.com)"
    echo "  -i IP_ADDRESS            IP address for server access (default: localhost)"
    echo "  -a AWS_ACCESS_KEY_ID     AWS access key ID (default: generated)"
    echo "  -s AWS_SECRET_ACCESS_KEY AWS secret access key (default: generated)"
    echo "  -r AWS_REGION            AWS region (default: us-east-1)"
    echo "  -v AWS_S3_SIGNATURE_VERSION S3 signature version (default: s3v4)"
    echo "  -t AWS_S3_ADDRESSING_STYLE S3 addressing style (default: path)"
    echo "  -h                       Show this help message"
    echo
    echo "Examples:"
    echo "  $0 -u myadmin -p mypass123"
    echo "  $0 -d mydomain.com -a my-access-key -s my-secret-key"
    echo "  $0 -i 192.168.1.100"
    exit 1
}

# Parse command line options
while getopts "u:p:d:i:a:s:r:v:t:h" opt; do
    case $opt in
        u) USERNAME="$OPTARG" ;;
        p) PASSWORD="$OPTARG" ;;
        d) DOMAIN="$OPTARG" ;;
        i) IP="$OPTARG" ;;
        a) AWS_ACCESS_KEY_ID="$OPTARG" ;;
        s) AWS_SECRET_ACCESS_KEY="$OPTARG" ;;
        r) AWS_REGION="$OPTARG" ;;
        v) AWS_S3_SIGNATURE_VERSION="$OPTARG" ;;
        t) AWS_S3_ADDRESSING_STYLE="$OPTARG" ;;
        h) usage ;;
        *) usage ;;
    esac
done

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
echo "Creating .env file with domain: $DOMAIN and IP: $IP"
cat > .env << EOL
# SeaweedFS environment configuration
# Generated on $(date)

# Domain configuration
DOMAIN=${DOMAIN}

# IP address for server access
IP=${IP}

# Docker group ID for API container socket access
DOCKER_GID=${DOCKER_GID}

# SeaweedFS URL endpoints (through nginx proxy)
SEAWEED_MASTER_URL=http://${IP}/master/1
SEAWEED_VOLUME_URL=http://${IP}/volume/1
SEAWEED_FILER_URL=http://${IP}:8888
SEAWEED_S3_URL=http://${IP}:9333

# Authentication for admin access
SEAWEED_AUTH_USER=${USERNAME}
SEAWEED_AUTH_PASSWORD=${PASSWORD}

# S3 API credentials
AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
AWS_DEFAULT_REGION=${AWS_REGION}
AWS_S3_SIGNATURE_VERSION=${AWS_S3_SIGNATURE_VERSION}
AWS_S3_ADDRESSING_STYLE=${AWS_S3_ADDRESSING_STYLE}
EOL

# Create S3 config file for SeaWeedFS
echo "Creating S3 config file for SeaWeedFS"
cat > s3.toml << EOL
# SeaWeedFS S3 Configuration
# Generated on $(date)
# Includes default CORS configuration for all buckets

[s3]
access_key = "${AWS_ACCESS_KEY_ID}"
secret_key = "${AWS_SECRET_ACCESS_KEY}"
region = "${AWS_REGION}"
signature_version = "${AWS_S3_SIGNATURE_VERSION}"
addressing_style = "${AWS_S3_ADDRESSING_STYLE}"

# Default CORS configuration for all buckets
[s3.cors]
allow_origins = ["*"]
allow_methods = ["GET", "PUT", "POST", "DELETE", "HEAD"]
allow_headers = ["*"]
expose_headers = ["ETag", "Content-Length", "Content-Type", "Content-Disposition"]
max_age = 3000
EOL

echo "✓ Created s3.toml file with default CORS configuration"

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

# Wait for services to start
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
echo "- Dashboard:     http://${IP}/"
echo "- Master 1:      http://${IP}/master/1/"
echo "- Volume 1:      http://${IP}/volume/1/"
echo "- Filer 1:       http://${IP}/filer/1/"
echo "- API Docs:      http://${IP}/api/docs"
echo ""
echo "🔗 Filer:"
echo "- Filer:         http://${IP}:8888/"
echo ""
echo "🔗 S3 API:"
echo "--------------------------------------"
echo "- S3 API:        http://${IP}:9333/"
echo ""
echo "🔐 Admin Authentication:"
echo "--------------------------------------"
echo "Username: $USERNAME"
echo "Password: $PASSWORD"
echo ""
echo "🔑 S3 API Credentials:"
echo "--------------------------------------"
echo "Access Key: $AWS_ACCESS_KEY_ID"
echo "Secret Key: $AWS_SECRET_ACCESS_KEY"
echo "Region: $AWS_REGION"
echo "Signature Version: $AWS_S3_SIGNATURE_VERSION"
echo "Addressing Style: $AWS_S3_ADDRESSING_STYLE"
echo ""
echo "📝 Environment Configuration:"
echo "--------------------------------------"
echo "All configuration has been saved to .env file"
echo "S3 config has been saved to s3_config.toml"
echo "Docker GID set to: $DOCKER_GID"
echo "IP address set to: $IP"
echo ""
echo "======================================================================================"
echo "✅ Setup complete! Access the dashboard at: http://${IP}/"
echo "======================================================================================"