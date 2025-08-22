#!/bin/bash

# Deployment Workflow Script
# Orchestrates build, containerization, and deployment process

set -e

# Configuration
PROJECT_NAME="${PROJECT_NAME:-codeflowops}"
ENVIRONMENT="${ENVIRONMENT:-staging}"
AWS_REGION="${AWS_REGION:-us-east-1}"
ECR_REPOSITORY="${PROJECT_NAME}-${ENVIRONMENT}"
BUILD_NUMBER="${BUILD_NUMBER:-$(date +%Y%m%d-%H%M%S)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

success() {
    echo -e "${GREEN}✅ $1${NC}"
}

warn() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

error() {
    echo -e "${RED}❌ $1${NC}"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "Checking deployment prerequisites..."
    
    # Check if Docker is running
    if ! docker info &> /dev/null; then
        error "Docker is not running. Please start Docker first."
    fi
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS CLI is not configured. Please run 'aws configure' first."
    fi
    
    # Check if repository analysis exists
    if [ ! -f "repository-analysis.json" ]; then
        warn "Repository analysis not found. Running analysis..."
        node scripts/analyze-repo.js .
    fi
    
    # Check if infrastructure outputs exist
    if [ ! -f "infrastructure-outputs.json" ]; then
        warn "Infrastructure outputs not found. Please run provision-infrastructure.sh first."
        exit 1
    fi
    
    success "Prerequisites check passed"
}

# Read deployment configuration
read_config() {
    log "Reading deployment configuration..."
    
    # Read from analysis
    FRAMEWORK=$(cat repository-analysis.json | jq -r '.framework // "unknown"')
    COMPUTE_TYPE=$(cat repository-analysis.json | jq -r '.infrastructure.compute // "container"')
    BUILD_COMMANDS=$(cat repository-analysis.json | jq -r '.deploymentConfig.buildCommands')
    
    # Read from infrastructure outputs
    VPC_ID=$(cat infrastructure-outputs.json | jq -r '.vpc_id.value // ""')
    LOAD_BALANCER_DNS=$(cat infrastructure-outputs.json | jq -r '.load_balancer_dns.value // ""')
    
    log "Framework: $FRAMEWORK"
    log "Compute Type: $COMPUTE_TYPE"
    log "VPC ID: $VPC_ID"
    
    success "Configuration loaded"
}

# Build application
build_application() {
    log "Building application..."
    
    case $FRAMEWORK in
        "Next.js")
            build_nextjs_app
            ;;
        "React")
            build_react_app
            ;;
        "Express.js")
            build_nodejs_app
            ;;
        *)
            build_generic_app
            ;;
    esac
    
    success "Application built successfully"
}

build_nextjs_app() {
    log "Building Next.js application..."
    
    # Install dependencies
    if [ -f "frontend/package.json" ]; then
        cd frontend
        npm ci
        npm run build
        cd ..
    else
        npm ci
        npm run build
    fi
}

build_react_app() {
    log "Building React application..."
    
    if [ -f "frontend/package.json" ]; then
        cd frontend
        npm ci
        npm run build
        cd ..
    else
        npm ci
        npm run build
    fi
}

build_nodejs_app() {
    log "Building Node.js application..."
    
    # Backend build
    if [ -f "backend/package.json" ]; then
        cd backend
        npm ci
        if [ -f "package.json" ] && jq -e '.scripts.build' package.json > /dev/null; then
            npm run build
        fi
        cd ..
    fi
    
    # Frontend build if exists
    if [ -f "frontend/package.json" ]; then
        cd frontend
        npm ci
        npm run build
        cd ..
    fi
}

build_generic_app() {
    log "Building generic application..."
    
    if [ -f "package.json" ]; then
        npm ci
        if jq -e '.scripts.build' package.json > /dev/null; then
            npm run build
        fi
    fi
}

# Generate Dockerfile if not exists
generate_dockerfile() {
    if [ -f "Dockerfile" ]; then
        log "Using existing Dockerfile"
        return
    fi
    
    log "Generating Dockerfile for $FRAMEWORK..."
    
    case $FRAMEWORK in
        "Next.js")
            generate_nextjs_dockerfile
            ;;
        "React")
            generate_react_dockerfile
            ;;
        "Express.js")
            generate_nodejs_dockerfile
            ;;
        *)
            generate_generic_dockerfile
            ;;
    esac
    
    success "Dockerfile generated"
}

generate_nextjs_dockerfile() {
    cat > Dockerfile << 'EOF'
# Next.js Dockerfile
FROM node:18-alpine AS base

# Install dependencies only when needed
FROM base AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

# Install dependencies based on the preferred package manager
COPY frontend/package*.json ./
RUN npm ci

# Rebuild the source code only when needed
FROM base AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY frontend/ .

RUN npm run build

# Production image, copy all the files and run next
FROM base AS runner
WORKDIR /app

ENV NODE_ENV production

RUN addgroup --system --gid 1001 nodejs
RUN adduser --system --uid 1001 nextjs

COPY --from=builder /app/public ./public

# Set the correct permission for prerender cache
RUN mkdir .next
RUN chown nextjs:nodejs .next

# Automatically leverage output traces to reduce image size
COPY --from=builder --chown=nextjs:nodejs /app/.next/standalone ./
COPY --from=builder --chown=nextjs:nodejs /app/.next/static ./.next/static

USER nextjs

EXPOSE 3000

ENV PORT 3000
ENV HOSTNAME "0.0.0.0"

CMD ["node", "server.js"]
EOF
}

generate_react_dockerfile() {
    cat > Dockerfile << 'EOF'
# React Dockerfile with Nginx
FROM node:18-alpine AS build

WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
EOF

    # Generate nginx.conf
    cat > nginx.conf << 'EOF'
events {
    worker_connections 1024;
}

http {
    include       /etc/nginx/mime.types;
    default_type  application/octet-stream;

    server {
        listen 80;
        location / {
            root   /usr/share/nginx/html;
            index  index.html index.htm;
            try_files $uri $uri/ /index.html;
        }
    }
}
EOF
}

generate_nodejs_dockerfile() {
    cat > Dockerfile << 'EOF'
# Node.js Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY backend/package*.json ./
RUN npm ci --only=production

# Copy application code
COPY backend/ .

# Create non-root user
RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

USER nodejs

EXPOSE 3000

CMD ["npm", "start"]
EOF
}

generate_generic_dockerfile() {
    cat > Dockerfile << 'EOF'
# Generic Node.js Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .

RUN addgroup -g 1001 -S nodejs
RUN adduser -S nodejs -u 1001

USER nodejs

EXPOSE 3000

CMD ["npm", "start"]
EOF
}

# Build and push Docker image
build_and_push_image() {
    log "Building and pushing Docker image..."
    
    # Get AWS account ID
    AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)
    ECR_URI="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
    IMAGE_URI="${ECR_URI}/${ECR_REPOSITORY}:${BUILD_NUMBER}"
    LATEST_URI="${ECR_URI}/${ECR_REPOSITORY}:latest"
    
    # Create ECR repository if it doesn't exist
    aws ecr describe-repositories --repository-names ${ECR_REPOSITORY} --region ${AWS_REGION} > /dev/null 2>&1 || \
    aws ecr create-repository --repository-name ${ECR_REPOSITORY} --region ${AWS_REGION}
    
    # Login to ECR
    aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_URI}
    
    # Build image
    docker build -t ${IMAGE_URI} -t ${LATEST_URI} .
    
    # Push image
    docker push ${IMAGE_URI}
    docker push ${LATEST_URI}
    
    # Save image URI for deployment
    echo ${IMAGE_URI} > image-uri.txt
    
    success "Docker image built and pushed: ${IMAGE_URI}"
}

# Deploy to ECS
deploy_to_ecs() {
    log "Deploying to ECS..."
    
    IMAGE_URI=$(cat image-uri.txt)
    CLUSTER_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
    SERVICE_NAME="${PROJECT_NAME}-${ENVIRONMENT}"
    
    # Update task definition with new image
    TASK_DEFINITION=$(aws ecs describe-task-definition \
        --task-definition ${SERVICE_NAME} \
        --region ${AWS_REGION} \
        --query 'taskDefinition' \
        --output json)
    
    # Update image URI in task definition
    NEW_TASK_DEFINITION=$(echo $TASK_DEFINITION | jq --arg IMAGE_URI "$IMAGE_URI" \
        '.containerDefinitions[0].image = $IMAGE_URI | del(.taskDefinitionArn) | del(.revision) | del(.status) | del(.requiresAttributes) | del(.placementConstraints) | del(.compatibilities) | del(.registeredAt) | del(.registeredBy)')
    
    # Register new task definition
    NEW_TASK_DEF_ARN=$(echo $NEW_TASK_DEFINITION | \
        aws ecs register-task-definition \
        --region ${AWS_REGION} \
        --cli-input-json file:///dev/stdin \
        --query 'taskDefinition.taskDefinitionArn' \
        --output text)
    
    # Update service
    aws ecs update-service \
        --cluster ${CLUSTER_NAME} \
        --service ${SERVICE_NAME} \
        --task-definition ${NEW_TASK_DEF_ARN} \
        --region ${AWS_REGION}
    
    # Wait for deployment to complete
    log "Waiting for deployment to complete..."
    aws ecs wait services-stable \
        --cluster ${CLUSTER_NAME} \
        --services ${SERVICE_NAME} \
        --region ${AWS_REGION}
    
    success "ECS deployment completed"
}

# Deploy static site to S3
deploy_to_s3() {
    log "Deploying static site to S3..."
    
    BUCKET_NAME="${PROJECT_NAME}-${ENVIRONMENT}-frontend"
    BUILD_DIR="frontend/build"
    
    if [ ! -d "$BUILD_DIR" ]; then
        BUILD_DIR="build"
    fi
    
    if [ ! -d "$BUILD_DIR" ]; then
        BUILD_DIR="dist"
    fi
    
    # Create S3 bucket if it doesn't exist
    aws s3 mb "s3://${BUCKET_NAME}" --region ${AWS_REGION} 2>/dev/null || true
    
    # Enable static website hosting
    aws s3 website "s3://${BUCKET_NAME}" \
        --index-document index.html \
        --error-document error.html
    
    # Upload files
    aws s3 sync ${BUILD_DIR} "s3://${BUCKET_NAME}" --delete
    
    # Make bucket public
    aws s3api put-bucket-policy \
        --bucket ${BUCKET_NAME} \
        --policy "{
            \"Version\": \"2012-10-17\",
            \"Statement\": [
                {
                    \"Sid\": \"PublicReadGetObject\",
                    \"Effect\": \"Allow\",
                    \"Principal\": \"*\",
                    \"Action\": \"s3:GetObject\",
                    \"Resource\": \"arn:aws:s3:::${BUCKET_NAME}/*\"
                }
            ]
        }"
    
    WEBSITE_URL="http://${BUCKET_NAME}.s3-website-${AWS_REGION}.amazonaws.com"
    echo $WEBSITE_URL > deployment-url.txt
    
    success "Static site deployed to: $WEBSITE_URL"
}

# Deploy application
deploy_application() {
    log "Deploying application..."
    
    case $COMPUTE_TYPE in
        "container")
            deploy_to_ecs
            ;;
        "static")
            deploy_to_s3
            ;;
        "serverless")
            # TODO: Implement Lambda deployment
            warn "Serverless deployment not yet implemented"
            ;;
        *)
            deploy_to_ecs
            ;;
    esac
    
    success "Application deployed successfully"
}

# Run post-deployment tasks
post_deployment() {
    log "Running post-deployment tasks..."
    
    # Save deployment info
    cat > deployment-info.json << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "buildNumber": "${BUILD_NUMBER}",
    "environment": "${ENVIRONMENT}",
    "framework": "${FRAMEWORK}",
    "computeType": "${COMPUTE_TYPE}",
    "imageUri": "$(cat image-uri.txt 2>/dev/null || echo 'N/A')",
    "deploymentUrl": "$(cat deployment-url.txt 2>/dev/null || echo 'N/A')"
}
EOF
    
    # Clean up temporary files
    rm -f tfplan image-uri.txt deployment-url.txt
    
    success "Post-deployment tasks completed"
}

# Main execution
main() {
    log "Starting deployment workflow for ${PROJECT_NAME} (${ENVIRONMENT})"
    
    check_prerequisites
    read_config
    build_application
    
    if [ "$COMPUTE_TYPE" != "static" ]; then
        generate_dockerfile
        build_and_push_image
    fi
    
    deploy_application
    post_deployment
    
    success "Deployment workflow completed!"
    
    # Display deployment info
    log "Deployment Summary:"
    cat deployment-info.json | jq .
    
    if [ -f "deployment-url.txt" ]; then
        DEPLOYMENT_URL=$(cat deployment-url.txt)
        log "🌐 Application URL: $DEPLOYMENT_URL"
    elif [ "$LOAD_BALANCER_DNS" != "" ]; then
        log "🌐 Application URL: http://$LOAD_BALANCER_DNS"
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
