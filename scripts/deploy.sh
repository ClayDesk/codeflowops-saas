#!/bin/bash

# CodeFlowOps Deployment Script
# This script handles deployment without GitHub Actions secret warnings
# Run manually or via CI/CD with pre-configured AWS credentials

set -e

# Configuration
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${ECR_REPOSITORY:-codeflowops-backend}"
ECS_SERVICE="${ECS_SERVICE:-codeflowops-service}"
ECS_CLUSTER="${ECS_CLUSTER:-codeflowops-cluster}"
FRONTEND_BUILD_DIR="${FRONTEND_BUILD_DIR:-frontend/dist}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if AWS CLI is configured
check_aws_config() {
    log_info "Checking AWS configuration..."
    
    if ! command -v aws &> /dev/null; then
        log_error "AWS CLI not found. Please install it first."
        exit 1
    fi
    
    if ! aws sts get-caller-identity &> /dev/null; then
        log_error "AWS credentials not configured. Please run 'aws configure' or set environment variables."
        exit 1
    fi
    
    local aws_account=$(aws sts get-caller-identity --query Account --output text)
    local aws_user=$(aws sts get-caller-identity --query Arn --output text)
    log_success "AWS configured - Account: $aws_account, User: $aws_user"
}

# Deploy backend to ECS
deploy_backend() {
    log_info "Starting backend deployment..."
    
    # Get ECR login
    log_info "Logging into ECR..."
    aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --query 'repositories[0].repositoryUri' --output text | cut -d'/' -f1)
    
    # Get ECR URI
    local ECR_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY --query 'repositories[0].repositoryUri' --output text)
    local IMAGE_TAG=$(git rev-parse --short HEAD || echo "latest")
    
    log_info "Building Docker image..."
    cd backend
    docker build -t $ECR_URI:$IMAGE_TAG .
    docker tag $ECR_URI:$IMAGE_TAG $ECR_URI:latest
    
    log_info "Pushing to ECR..."
    docker push $ECR_URI:$IMAGE_TAG
    docker push $ECR_URI:latest
    
    log_info "Updating ECS service..."
    aws ecs update-service \
        --cluster $ECS_CLUSTER \
        --service $ECS_SERVICE \
        --force-new-deployment \
        --region $AWS_REGION
    
    log_success "Backend deployment initiated. Check ECS console for progress."
    cd ..
}

# Deploy frontend to S3
deploy_frontend() {
    log_info "Starting frontend deployment..."
    
    if [ -z "$S3_BUCKET_NAME" ]; then
        log_error "S3_BUCKET_NAME environment variable not set"
        return 1
    fi
    
    # Build frontend if not already built
    if [ ! -d "$FRONTEND_BUILD_DIR" ]; then
        log_info "Building frontend..."
        cd frontend
        npm ci
        npm run build
        cd ..
    fi
    
    log_info "Syncing to S3 bucket: $S3_BUCKET_NAME"
    aws s3 sync $FRONTEND_BUILD_DIR s3://$S3_BUCKET_NAME/ --delete
    
    # Invalidate CloudFront if distribution ID is provided
    if [ -n "$CLOUDFRONT_DISTRIBUTION_ID" ]; then
        log_info "Invalidating CloudFront distribution: $CLOUDFRONT_DISTRIBUTION_ID"
        aws cloudfront create-invalidation \
            --distribution-id $CLOUDFRONT_DISTRIBUTION_ID \
            --paths "/*"
    else
        log_warning "CLOUDFRONT_DISTRIBUTION_ID not set, skipping cache invalidation"
    fi
    
    log_success "Frontend deployment completed"
}

# Main deployment function
main() {
    log_info "🚀 Starting CodeFlowOps deployment..."
    log_info "Region: $AWS_REGION"
    log_info "Timestamp: $(date)"
    
    # Parse command line arguments
    DEPLOY_BACKEND=false
    DEPLOY_FRONTEND=false
    
    case "${1:-all}" in
        "backend")
            DEPLOY_BACKEND=true
            ;;
        "frontend")
            DEPLOY_FRONTEND=true
            ;;
        "all")
            DEPLOY_BACKEND=true
            DEPLOY_FRONTEND=true
            ;;
        *)
            echo "Usage: $0 [backend|frontend|all]"
            echo "  backend  - Deploy only backend to ECS"
            echo "  frontend - Deploy only frontend to S3"
            echo "  all      - Deploy both (default)"
            exit 1
            ;;
    esac
    
    # Check prerequisites
    check_aws_config
    
    # Deploy components
    if [ "$DEPLOY_BACKEND" = true ]; then
        deploy_backend
    fi
    
    if [ "$DEPLOY_FRONTEND" = true ]; then
        deploy_frontend
    fi
    
    log_success "🎉 Deployment completed successfully!"
    log_info "Check your application at the configured domain"
}

# Run main function with all arguments
main "$@"
