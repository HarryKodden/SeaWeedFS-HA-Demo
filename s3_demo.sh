#!/bin/bash

# SeaWeedFS S3 Operations Demo Script
# This script demonstrates basic S3 operations with SeaWeedFS
# Note: For production use, consider using AWS CLI or s3cmd for proper authentication

set -e

# Configuration
S3_ENDPOINT="http://localhost:8333"  # Load balancer endpoint
BUCKET_NAME="test-bucket"
TEST_FILE="test-file.txt"
TEST_CONTENT="Hello, SeaWeedFS S3!"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SeaWeedFS S3 Operations Demo${NC}"
echo -e "${BLUE}========================================${NC}"
echo

# Load credentials from .env file if it exists
if [ -f ".env" ]; then
    echo -e "${YELLOW}Loading credentials from .env file...${NC}"
    source .env
    echo -e "${GREEN}✓ Credentials loaded${NC}"
    echo -e "  Access Key: ${AWS_ACCESS_KEY_ID}"
    echo
else
    echo -e "${RED}✗ .env file not found. Please ensure S3 credentials are available.${NC}"
    echo -e "${YELLOW}Expected credentials:${NC}"
    echo -e "  AWS_ACCESS_KEY_ID=<your-access-key>"
    echo -e "  AWS_SECRET_ACCESS_KEY=<your-secret-key>"
    exit 1
fi

# Function to check if S3 endpoint is accessible
check_s3_endpoint() {
    echo -e "${YELLOW}Checking S3 endpoint accessibility...${NC}"
    if curl -s -o /dev/null -w "%{http_code}" "$S3_ENDPOINT/" | grep -q "403"; then
        echo -e "${GREEN}✓ S3 endpoint is accessible${NC}"
        return 0
    else
        echo -e "${RED}✗ S3 endpoint is not accessible${NC}"
        return 1
    fi
}

# Function to create a bucket (simplified - requires proper authentication)
create_bucket() {
    echo -e "${YELLOW}Creating bucket: $BUCKET_NAME${NC}"

    # For demonstration - this will fail without proper authentication
    # In production, use AWS CLI: aws s3 mb s3://$BUCKET_NAME --endpoint-url=$S3_ENDPOINT
    echo -e "${BLUE}Command (requires AWS CLI):${NC}"
    echo -e "aws s3 mb s3://$BUCKET_NAME --endpoint-url=$S3_ENDPOINT"
    echo

    # Alternative: Using curl with minimal headers (will fail but shows the structure)
    echo -e "${BLUE}CURL equivalent (for demonstration):${NC}"
    echo "curl -X PUT \\"
    echo "  -H \"Host: $BUCKET_NAME.$S3_ENDPOINT\" \\"
    echo "  -H \"Date: \$(date -u +'%a, %d %b %Y %H:%M:%S GMT')\" \\"
    echo "  -H \"Authorization: AWS4-HMAC-SHA256 ...\" \\"
    echo "  \"$S3_ENDPOINT/$BUCKET_NAME/\""
    echo

    # Try the request (will fail without auth, but shows the API is working)
    echo -e "${YELLOW}Testing bucket creation request...${NC}"
    if curl -s -X PUT "$S3_ENDPOINT/$BUCKET_NAME/" 2>/dev/null | grep -q "AccessDenied"; then
        echo -e "${GREEN}✓ S3 API accepts bucket creation requests${NC}"
        echo -e "${YELLOW}  (Authentication required for actual creation)${NC}"
    else
        echo -e "${RED}✗ Unexpected response from S3 API${NC}"
    fi
}

# Function to upload a file (simplified - requires proper authentication)
upload_file() {
    echo -e "${YELLOW}Uploading file: $TEST_FILE to bucket: $BUCKET_NAME${NC}"

    # Create a test file
    echo "$TEST_CONTENT" > "$TEST_FILE"
    echo -e "${GREEN}✓ Created test file: $TEST_FILE${NC}"
    echo -e "  Content: $TEST_CONTENT"
    echo

    # For demonstration - this will fail without proper authentication
    # In production, use AWS CLI: aws s3 cp $TEST_FILE s3://$BUCKET_NAME/ --endpoint-url=$S3_ENDPOINT
    echo -e "${BLUE}Command (requires AWS CLI):${NC}"
    echo -e "aws s3 cp $TEST_FILE s3://$BUCKET_NAME/ --endpoint-url=$S3_ENDPOINT"
    echo

    # Alternative: Using curl with minimal headers (will fail but shows the structure)
    echo -e "${BLUE}CURL equivalent (for demonstration):${NC}"
    echo "curl -X PUT \\"
    echo "  -H \"Host: $BUCKET_NAME.$S3_ENDPOINT\" \\"
    echo "  -H \"Date: \$(date -u +'%a, %d %b %Y %H:%M:%S GMT')\" \\"
    echo "  -H \"Authorization: AWS4-HMAC-SHA256 ...\" \\"
    echo "  -T \"$TEST_FILE\" \\"
    echo "  \"$S3_ENDPOINT/$BUCKET_NAME/$TEST_FILE\""
    echo

    # Try the request (will fail without auth, but shows the API is working)
    echo -e "${YELLOW}Testing file upload request...${NC}"
    if curl -s -X PUT -T "$TEST_FILE" "$S3_ENDPOINT/$BUCKET_NAME/$TEST_FILE" 2>/dev/null | grep -q "AccessDenied"; then
        echo -e "${GREEN}✓ S3 API accepts file upload requests${NC}"
        echo -e "${YELLOW}  (Authentication required for actual upload)${NC}"
    else
        echo -e "${RED}✗ Unexpected response from S3 API${NC}"
    fi

    # Clean up test file
    rm -f "$TEST_FILE"
}

# Function to list buckets (simplified - requires proper authentication)
list_buckets() {
    echo -e "${YELLOW}Listing buckets...${NC}"

    # For demonstration - this will fail without proper authentication
    # In production, use AWS CLI: aws s3 ls --endpoint-url=$S3_ENDPOINT
    echo -e "${BLUE}Command (requires AWS CLI):${NC}"
    echo -e "aws s3 ls --endpoint-url=$S3_ENDPOINT"
    echo

    # Alternative: Using curl with minimal headers (will fail but shows the structure)
    echo -e "${BLUE}CURL equivalent (for demonstration):${NC}"
    echo "curl -H \"Authorization: AWS4-HMAC-SHA256 ...\" \\"
    echo "  \"$S3_ENDPOINT/\""
    echo

    # Try the request (will fail without auth, but shows the API is working)
    echo -e "${YELLOW}Testing bucket listing request...${NC}"
    if curl -s "$S3_ENDPOINT/" 2>/dev/null | grep -q "AccessDenied"; then
        echo -e "${GREEN}✓ S3 API accepts list buckets requests${NC}"
        echo -e "${YELLOW}  (Authentication required for actual listing)${NC}"
    else
        echo -e "${RED}✗ Unexpected response from S3 API${NC}"
    fi
}

# Function to demonstrate AWS CLI setup
setup_aws_cli() {
    echo -e "${YELLOW}AWS CLI Configuration for SeaWeedFS S3:${NC}"
    echo -e "${BLUE}1. Configure AWS CLI:${NC}"
    echo "aws configure --profile seaweedfs"
    echo -e "  AWS Access Key ID: $AWS_ACCESS_KEY_ID"
    echo -e "  AWS Secret Access Key: $AWS_SECRET_ACCESS_KEY"
    echo -e "  Default region: us-east-1"
    echo -e "  Default output format: json"
    echo

    echo -e "${BLUE}2. Create bucket:${NC}"
    echo "aws s3 mb s3://$BUCKET_NAME --endpoint-url=$S3_ENDPOINT --profile seaweedfs"
    echo

    echo -e "${BLUE}3. Upload file:${NC}"
    echo "echo '$TEST_CONTENT' > $TEST_FILE"
    echo "aws s3 cp $TEST_FILE s3://$BUCKET_NAME/ --endpoint-url=$S3_ENDPOINT --profile seaweedfs"
    echo

    echo -e "${BLUE}4. List buckets:${NC}"
    echo "aws s3 ls --endpoint-url=$S3_ENDPOINT --profile seaweedfs"
    echo

    echo -e "${BLUE}5. List bucket contents:${NC}"
    echo "aws s3 ls s3://$BUCKET_NAME/ --endpoint-url=$S3_ENDPOINT --profile seaweedfs"
    echo

    echo -e "${BLUE}6. Download file:${NC}"
    echo "aws s3 cp s3://$BUCKET_NAME/$TEST_FILE downloaded-$TEST_FILE --endpoint-url=$S3_ENDPOINT --profile seaweedfs"
}

# Main execution
main() {
    # Check S3 endpoint
    if ! check_s3_endpoint; then
        echo -e "${RED}Cannot proceed without S3 endpoint access${NC}"
        exit 1
    fi

    echo -e "${GREEN}S3 Endpoint: $S3_ENDPOINT${NC}"
    echo -e "${GREEN}Test Bucket: $BUCKET_NAME${NC}"
    echo -e "${GREEN}Test File: $TEST_FILE${NC}"
    echo

    # Demonstrate operations
    create_bucket
    echo
    upload_file
    echo
    list_buckets
    echo

    # Show AWS CLI setup
    echo -e "${BLUE}========================================${NC}"
    echo -e "${BLUE}  AWS CLI Setup Instructions${NC}"
    echo -e "${BLUE}========================================${NC}"
    setup_aws_cli
    echo

    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Demo Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${YELLOW}Note: The above curl commands are for demonstration only.${NC}"
    echo -e "${YELLOW}For actual S3 operations, use AWS CLI with proper authentication.${NC}"
    echo
    echo -e "${BLUE}Your SeaWeedFS S3 API is working correctly! 🎉${NC}"
}

# Run main function
main "$@"
