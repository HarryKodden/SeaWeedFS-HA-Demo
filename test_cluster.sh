#!/bin/bash
# Test script for SeaweedFS HA setup

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}=====================================${NC}"
echo -e "${YELLOW}      SEAWEEDFS HA CLUSTER TEST      ${NC}"
echo -e "${YELLOW}=====================================${NC}"
echo

# Check if the cluster is running
echo -e "Checking if containers are running..."
if [ "$(docker ps | grep demo-nginx-1 | wc -l)" -eq 0 ]; then
    echo -e "${RED}[FAILED]${NC} Nginx container not running!"
    echo -e "Run ${YELLOW}docker compose up -d${NC} to start the cluster"
    exit 1
else
    echo -e "${GREEN}[OK]${NC} Nginx container is running"
fi

# Test Dashboard access (port 9080)
echo -e "\nTesting Dashboard access on port 9080..."
if curl -s -o /dev/null -w "%{http_code}" -u admin:seaweedadmin http://localhost:9080/ | grep -q "200"; then
    echo -e "${GREEN}[OK]${NC} Dashboard is accessible"
else
    echo -e "${RED}[FAILED]${NC} Dashboard is not accessible"
fi

# Test S3 API access (port 9333)
echo -e "\nTesting S3 API access on port 9333..."
if curl -s -o /dev/null -I -w "%{http_code}" http://localhost:9333/ | grep -q "405\|403\|401\|400"; then
    echo -e "${GREEN}[OK]${NC} S3 API is accessible"
else
    echo -e "${RED}[FAILED]${NC} S3 API is not accessible"
fi

# Test cluster admin dashboard (port 9080 - consolidated)
echo -e "\nTesting Cluster Admin dashboard on port 9080..."
if curl -s -o /dev/null -I -w "%{http_code}" -u admin:seaweedadmin http://localhost:9080/ | grep -q "200"; then
    echo -e "${GREEN}[OK]${NC} Cluster Admin dashboard is accessible"
else
    echo -e "${RED}[FAILED]${NC} Cluster Admin dashboard is not accessible"
fi

# Load credentials from .env file
if [ -f .env ]; then
    source .env
    echo -e "\nTesting with credentials from .env file:"
    echo -e "Username: ${YELLOW}${SEAWEED_AUTH_USER}${NC}"
    echo -e "S3 Access Key: ${YELLOW}${AWS_ACCESS_KEY_ID}${NC}"
    
    # Test authenticated access to cluster admin
    echo -e "\nTesting authenticated access to Cluster Admin dashboard..."
    if curl -s -o /dev/null -w "%{http_code}" -u "${SEAWEED_AUTH_USER}:${SEAWEED_AUTH_PASSWORD}" http://localhost:9080/ | grep -q "200"; then
        echo -e "${GREEN}[OK]${NC} Authenticated access to Cluster Admin dashboard works"
    else
        echo -e "${RED}[FAILED]${NC} Authenticated access to Cluster Admin dashboard failed"
    fi
else
    echo -e "\n${RED}[WARNING]${NC} .env file not found. Cannot test with credentials."
fi

echo -e "\n${YELLOW}=====================================${NC}"
echo -e "${YELLOW}          TEST COMPLETED             ${NC}"
echo -e "${YELLOW}=====================================${NC}"
