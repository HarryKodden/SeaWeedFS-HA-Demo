#!/bin/bash

# SeaWeedFS S3 Operations Demo Script
# This script demonstrates and executes basic S3 operations with SeaWeedFS
# Requires AWS CLI to be installed and configured

set -e

# Configuration
S3_ENDPOINT="http://localhost:8333"  # Load balancer endpoint
BUCKET_NAME="test-bucket"
TEST_FILE="test-file.txt"
TEST_CONTENT="Hello, SeaWeedFS S3!"
AWS_PROFILE="seaweedfs"

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

# Function to check if AWS CLI is installed
check_aws_cli() {
    echo -e "${YELLOW}Checking AWS CLI installation...${NC}"
    if ! command -v aws &> /dev/null; then
        echo -e "${RED}✗ AWS CLI is not installed${NC}"
        echo -e "${YELLOW}Please install AWS CLI:${NC}"
        echo -e "  Ubuntu/Debian: sudo apt install awscli"
        echo -e "  macOS: brew install awscli"
        echo -e "  Or download from: https://aws.amazon.com/cli/"
        exit 1
    fi
    echo -e "${GREEN}✓ AWS CLI is installed${NC}"
    echo -e "  Version: $(aws --version)"
    echo
}

# Function to configure AWS CLI
configure_aws_cli() {
    echo -e "${YELLOW}Configuring AWS CLI for SeaWeedFS...${NC}"
    
    # Create AWS config directory if it doesn't exist
    mkdir -p ~/.aws
    
    # Configure the profile
    aws configure set aws_access_key_id "$AWS_ACCESS_KEY_ID" --profile "$AWS_PROFILE"
    aws configure set aws_secret_access_key "$AWS_SECRET_ACCESS_KEY" --profile "$AWS_PROFILE"
    aws configure set region "$AWS_DEFAULT_REGION" --profile "$AWS_PROFILE"
    aws configure set output "json" --profile "$AWS_PROFILE"
    
    # Set S3 signature version to S3v4 for SeaWeedFS compatibility
    aws configure set s3.signature_version "$AWS_S3_SIGNATURE_VERSION" --profile "$AWS_PROFILE"
    aws configure set s3.addressing_style "$AWS_S3_ADDRESSING_STYLE" --profile "$AWS_PROFILE"
    
    echo -e "${GREEN}✓ AWS CLI configured with profile: $AWS_PROFILE${NC}"
    echo -e "  Access Key: ${AWS_ACCESS_KEY_ID:0:8}..."
    echo -e "  Region: $AWS_DEFAULT_REGION"
    echo -e "  Signature Version: $AWS_S3_SIGNATURE_VERSION"
    echo -e "  Addressing Style: $AWS_S3_ADDRESSING_STYLE"
    echo
}

# Function to check if S3 endpoint is accessible
check_s3_endpoint() {
    echo -e "${YELLOW}Checking S3 endpoint accessibility...${NC}"
    if curl -s -o /dev/null -w "%{http_code}" "$S3_ENDPOINT/" | grep -q "403\|200"; then
        echo -e "${GREEN}✓ S3 endpoint is accessible${NC}"
        return 0
    else
        echo -e "${RED}✗ S3 endpoint is not accessible${NC}"
        return 1
    fi
}

# Function to create a bucket
create_bucket() {
    echo -e "${YELLOW}Creating bucket: $BUCKET_NAME${NC}"
    
    if aws s3 ls "s3://$BUCKET_NAME" --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE" &> /dev/null; then
        echo -e "${YELLOW}⚠ Bucket $BUCKET_NAME already exists${NC}"
        return 0
    fi
    
    if aws s3 mb "s3://$BUCKET_NAME" --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE"; then
        echo -e "${GREEN}✓ Bucket $BUCKET_NAME created successfully${NC}"
    else
        echo -e "${RED}✗ Failed to create bucket $BUCKET_NAME${NC}"
        return 1
    fi
}

# Function to upload a file
upload_file() {
    echo -e "${YELLOW}Uploading file: $TEST_FILE to bucket: $BUCKET_NAME${NC}"
    
    # Create a test file
    echo "$TEST_CONTENT" > "$TEST_FILE"
    echo -e "${GREEN}✓ Created test file: $TEST_FILE${NC}"
    echo -e "  Content: $TEST_CONTENT"
    echo
    
    if aws s3 cp "$TEST_FILE" "s3://$BUCKET_NAME/" --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE"; then
        echo -e "${GREEN}✓ File $TEST_FILE uploaded successfully${NC}"
    else
        echo -e "${RED}✗ Failed to upload file $TEST_FILE${NC}"
        rm -f "$TEST_FILE"
        return 1
    fi
    
    # Clean up test file
    rm -f "$TEST_FILE"
}

# Function to list buckets
list_buckets() {
    echo -e "${YELLOW}Listing buckets...${NC}"
    
    if buckets=$(aws s3 ls --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE" 2>/dev/null); then
        if [ -z "$buckets" ]; then
            echo -e "${YELLOW}⚠ No buckets found${NC}"
        else
            echo -e "${GREEN}✓ Buckets:${NC}"
            echo "$buckets"
        fi
    else
        echo -e "${RED}✗ Failed to list buckets${NC}"
        return 1
    fi
}

# Function to list bucket contents
list_bucket_contents() {
    echo -e "${YELLOW}Listing contents of bucket: $BUCKET_NAME${NC}"
    
    if contents=$(aws s3 ls "s3://$BUCKET_NAME/" --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE" 2>/dev/null); then
        if [ -z "$contents" ]; then
            echo -e "${YELLOW}⚠ Bucket $BUCKET_NAME is empty${NC}"
        else
            echo -e "${GREEN}✓ Bucket contents:${NC}"
            echo "$contents"
        fi
    else
        echo -e "${RED}✗ Failed to list bucket contents${NC}"
        return 1
    fi
}

# Function to download a file
download_file() {
    echo -e "${YELLOW}Downloading file: $TEST_FILE from bucket: $BUCKET_NAME${NC}"
    local download_file="downloaded-$TEST_FILE"
    
    if aws s3 cp "s3://$BUCKET_NAME/$TEST_FILE" "$download_file" --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE"; then
        echo -e "${GREEN}✓ File downloaded successfully: $download_file${NC}"
        echo -e "  Content: $(cat "$download_file")"
        rm -f "$download_file"
    else
        echo -e "${RED}✗ Failed to download file $TEST_FILE${NC}"
        return 1
    fi
}

# Function to delete a file
delete_file() {
    echo -e "${YELLOW}Deleting file: $TEST_FILE from bucket: $BUCKET_NAME${NC}"
    
    if aws s3 rm "s3://$BUCKET_NAME/$TEST_FILE" --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE"; then
        echo -e "${GREEN}✓ File $TEST_FILE deleted successfully${NC}"
    else
        echo -e "${RED}✗ Failed to delete file $TEST_FILE${NC}"
        return 1
    fi
}

# Function to delete a bucket
delete_bucket() {
    echo -e "${YELLOW}Deleting bucket: $BUCKET_NAME${NC}"
    
    if aws s3 rb "s3://$BUCKET_NAME" --endpoint-url="$S3_ENDPOINT" --profile="$AWS_PROFILE"; then
        echo -e "${GREEN}✓ Bucket $BUCKET_NAME deleted successfully${NC}"
    else
        echo -e "${RED}✗ Failed to delete bucket $BUCKET_NAME${NC}"
        return 1
    fi
}

# Function to show usage
usage() {
    echo -e "${BLUE}Usage: $0 [OPTIONS]${NC}"
    echo
    echo -e "${YELLOW}Options:${NC}"
    echo -e "  -h, --help          Show this help message"
    echo -e "  -c, --create        Create bucket and upload test file"
    echo -e "  -l, --list          List buckets and contents"
    echo -e "  -d, --download      Download test file"
    echo -e "  -r, --delete        Delete test file and bucket"
    echo -e "  -a, --all           Run all operations (create, list, download, delete)"
    echo
    echo -e "${YELLOW}Examples:${NC}"
    echo -e "  $0 --create         # Create bucket and upload file"
    echo -e "  $0 --all            # Run complete demo"
    echo -e "  $0 --list           # List buckets and contents"
}

# Main execution
main() {
    # Parse command line arguments
    local run_create=false
    local run_list=false
    local run_download=false
    local run_delete=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            -h|--help)
                usage
                exit 0
                ;;
            -c|--create)
                run_create=true
                shift
                ;;
            -l|--list)
                run_list=true
                shift
                ;;
            -d|--download)
                run_download=true
                shift
                ;;
            -r|--delete)
                run_delete=true
                shift
                ;;
            -a|--all)
                run_create=true
                run_list=true
                run_download=true
                run_delete=true
                shift
                ;;
            *)
                echo -e "${RED}Unknown option: $1${NC}"
                usage
                exit 1
                ;;
        esac
    done
    
    # If no options specified, run all
    if [[ "$run_create" == false && "$run_list" == false && "$run_download" == false && "$run_delete" == false ]]; then
        run_create=true
        run_list=true
        run_download=true
        run_delete=true
    fi
    
    # Load credentials from .env file if it exists
    if [ -f ".env" ]; then
        echo -e "${YELLOW}Loading credentials from .env file...${NC}"
        source .env
        echo -e "${GREEN}✓ Credentials loaded${NC}"
        echo -e "  Access Key: ${AWS_ACCESS_KEY_ID:0:8}..."
        echo -e "  Secret Key: ${AWS_SECRET_ACCESS_KEY:0:8}..."
        echo -e "  Region: $AWS_DEFAULT_REGION"
        echo -e "  Signature Version: $AWS_S3_SIGNATURE_VERSION"
        echo -e "  Addressing Style: $AWS_S3_ADDRESSING_STYLE"
        echo
    else
        echo -e "${RED}✗ .env file not found. Please ensure S3 credentials are available.${NC}"
        echo -e "${YELLOW}Expected credentials:${NC}"
        echo -e "  AWS_ACCESS_KEY_ID=<your-access-key>"
        echo -e "  AWS_SECRET_ACCESS_KEY=<your-secret-key>"
        echo -e "  AWS_DEFAULT_REGION=us-east-1"
        echo -e "  AWS_S3_SIGNATURE_VERSION=s3v4"
        echo -e "  AWS_S3_ADDRESSING_STYLE=path"
        exit 1
    fi
    
    # Check prerequisites
    check_aws_cli
    configure_aws_cli
    
    if ! check_s3_endpoint; then
        echo -e "${RED}Cannot proceed without S3 endpoint access${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}S3 Endpoint: $S3_ENDPOINT${NC}"
    echo -e "${GREEN}Test Bucket: $BUCKET_NAME${NC}"
    echo -e "${GREEN}Test File: $TEST_FILE${NC}"
    echo -e "${GREEN}AWS Profile: $AWS_PROFILE${NC}"
    echo
    
    # Execute operations
    if [[ "$run_create" == true ]]; then
        echo -e "${BLUE}=== Creating Bucket and Uploading File ===${NC}"
        create_bucket
        upload_file
        echo
    fi
    
    if [[ "$run_list" == true ]]; then
        echo -e "${BLUE}=== Listing Buckets and Contents ===${NC}"
        list_buckets
        list_bucket_contents
        echo
    fi
    
    if [[ "$run_download" == true ]]; then
        echo -e "${BLUE}=== Downloading File ===${NC}"
        download_file
        echo
    fi
    
    if [[ "$run_delete" == true ]]; then
        echo -e "${BLUE}=== Deleting File and Bucket ===${NC}"
        delete_file
        delete_bucket
        echo
    fi
    
    echo -e "${GREEN}========================================${NC}"
    echo -e "${GREEN}  Demo Complete!${NC}"
    echo -e "${GREEN}========================================${NC}"
    echo -e "${BLUE}Your SeaWeedFS S3 API is working correctly! 🎉${NC}"
}

# Run main function
main "$@"