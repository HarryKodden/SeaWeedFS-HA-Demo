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
#   4. Starts the SeaweedFS HA cluster with 3 masters, 3 volumes, and 2 filers

# Default values
DEFAULT_USERNAME="admin"
DEFAULT_PASSWORD="seaweedadmin"
DEFAULT_DOMAIN="example.com"

# Generate random S3 credentials if needed
RANDOM_ACCESS_KEY=$(cat /dev/urandom | tr -dc 'A-Z0-9' | fold -w 32 | head -n 1)
RANDOM_SECRET_KEY=$(cat /dev/urandom | tr -dc 'a-zA-Z0-9' | fold -w 40 | head -n 1)

# Use provided credentials or defaults
USERNAME=${1:-$DEFAULT_USERNAME}
PASSWORD=${2:-$DEFAULT_PASSWORD}
DOMAIN=${3:-$DEFAULT_DOMAIN}

echo "Setting up SeaweedFS HA cluster..."

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

# SeaweedFS URL endpoints
SEAWEED_MASTER_URL=http://localhost:9500/master/1
SEAWEED_VOLUME_URL=http://localhost:9500/volume/1
SEAWEED_FILER_URL=http://localhost:9080
SEAWEED_S3_URL=http://localhost:9333

# Domain-based URLs (if using domain)
#SEAWEED_MASTER_URL=https://seaweed-ha-cluster.${DOMAIN}/master/1
#SEAWEED_VOLUME_URL=https://seaweed-ha-cluster.${DOMAIN}/volume/1
#SEAWEED_FILER_URL=https://seaweed-ha.${DOMAIN}
#SEAWEED_S3_URL=https://seaweed-ha-s3.${DOMAIN}

# Authentication for admin access
SEAWEED_AUTH_USER=${USERNAME}
SEAWEED_AUTH_PASSWORD=${PASSWORD}

# S3 API credentials
AWS_ACCESS_KEY_ID=${RANDOM_ACCESS_KEY}
AWS_SECRET_ACCESS_KEY=${RANDOM_SECRET_KEY}
EOL

# Check if docker compose is available (newer version without hyphen)
if ! command -v docker &> /dev/null; then
    echo "docker not found. Please install Docker first."
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
sleep 10

# Check container status
docker compose ps

echo "======================================================================================"
echo "🌟 SeaweedFS HA cluster is now running! 🌟"
echo "======================================================================================"
echo ""
echo "📂 Local Access (via port forwarding):"
echo "--------------------------------------"
echo "- Filer:  http://localhost:9080/"
echo "- S3 API: http://localhost:9333/"
echo "- Cluster Admin Dashboard (requires authentication): http://localhost:9334/"
echo "- Master1 (requires authentication): http://localhost:9334/master/1/"
echo "- Volume1 (requires authentication): http://localhost:9334/volume/1/"
echo ""
echo "🌐 Domain-based Access (when deployed with domain: $DOMAIN):"
echo "--------------------------------------"
echo "- Filer:  https://seaweed-ha.${DOMAIN}"
echo "- S3 API: https://seaweed-ha-s3.${DOMAIN}"
echo "- Cluster Admin: https://seaweed-ha-cluster.${DOMAIN}"
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
echo "The Jupyter notebook will automatically use these settings"
echo ""
echo "======================================================================================"
