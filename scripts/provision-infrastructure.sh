#!/bin/bash

# Infrastructure Provisioning Script
# Creates backend stack using Terraform with dynamic configuration

set -e

# Configuration
PROJECT_NAME="${PROJECT_NAME:-codeflowops}"
ENVIRONMENT="${ENVIRONMENT:-staging}"
AWS_REGION="${AWS_REGION:-us-east-1}"
TERRAFORM_DIR="./terraform_workspace"

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
    log "Checking prerequisites..."
    
    # Check if terraform is installed
    if ! command -v terraform &> /dev/null; then
        error "Terraform is not installed. Please install Terraform first."
    fi
    
    # Check if AWS CLI is configured
    if ! aws sts get-caller-identity &> /dev/null; then
        error "AWS CLI is not configured. Please run 'aws configure' first."
    fi
    
    # Check if analysis file exists
    if [ ! -f "repository-analysis.json" ]; then
        warn "Repository analysis not found. Running analysis first..."
        node scripts/analyze-repo.js .
    fi
    
    success "Prerequisites check passed"
}

# Generate Terraform configuration based on analysis
generate_terraform_config() {
    log "Generating Terraform configuration..."
    
    # Read analysis results
    local framework=$(cat repository-analysis.json | jq -r '.framework // "unknown"')
    local database=$(cat repository-analysis.json | jq -r '.infrastructure.database // "none"')
    local compute=$(cat repository-analysis.json | jq -r '.infrastructure.compute // "container"')
    local cache=$(cat repository-analysis.json | jq -r '.infrastructure.cache // "none"')
    
    # Create terraform directory
    mkdir -p ${TERRAFORM_DIR}
    
    # Generate main.tf
    cat > ${TERRAFORM_DIR}/main.tf << EOF
# CodeFlowOps Infrastructure - Auto-generated
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
  
  backend "s3" {
    bucket = "${PROJECT_NAME}-terraform-state"
    key    = "${ENVIRONMENT}/terraform.tfstate"
    region = "${AWS_REGION}"
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Project     = "${PROJECT_NAME}"
      Environment = "${ENVIRONMENT}"
      ManagedBy   = "Terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
EOF

    # Generate variables.tf
    cat > ${TERRAFORM_DIR}/variables.tf << EOF
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "${PROJECT_NAME}"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "${ENVIRONMENT}"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "${AWS_REGION}"
}

variable "framework" {
  description = "Application framework"
  type        = string
  default     = "${framework}"
}

variable "enable_database" {
  description = "Enable database resources"
  type        = bool
  default     = $([ "$database" != "none" ] && echo "true" || echo "false")
}

variable "database_engine" {
  description = "Database engine"
  type        = string
  default     = "$(echo $database | tr '[:upper:]' '[:lower:]')"
}

variable "enable_cache" {
  description = "Enable Redis cache"
  type        = bool
  default     = $([ "$cache" != "none" ] && echo "true" || echo "false")
}

variable "compute_type" {
  description = "Compute deployment type"
  type        = string
  default     = "${compute}"
}
EOF

    # Generate networking.tf
    cat > ${TERRAFORM_DIR}/networking.tf << EOF
# VPC Configuration
resource "aws_vpc" "main" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_hostnames = true
  enable_dns_support   = true
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count = 2
  
  vpc_id                  = aws_vpc.main.id
  cidr_block              = "10.0.\${count.index + 1}.0/24"
  availability_zone       = data.aws_availability_zones.available.names[count.index]
  map_public_ip_on_launch = true
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-public-\${count.index + 1}"
    Type = "Public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count = 2
  
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.\${count.index + 10}.0/24"
  availability_zone = data.aws_availability_zones.available.names[count.index]
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-private-\${count.index + 1}"
    Type = "Private"
  }
}

# Route Tables
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id
  
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-public-rt"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
EOF

    # Generate compute resources based on type
    if [ "$compute" = "container" ]; then
        generate_ecs_config
    elif [ "$compute" = "serverless" ]; then
        generate_lambda_config
    elif [ "$compute" = "static" ]; then
        generate_s3_config
    fi
    
    # Generate database config if needed
    if [ "$database" != "none" ]; then
        generate_database_config "$database"
    fi
    
    # Generate cache config if needed
    if [ "$cache" != "none" ]; then
        generate_cache_config
    fi
    
    # Generate outputs.tf
    cat > ${TERRAFORM_DIR}/outputs.tf << EOF
output "vpc_id" {
  description = "VPC ID"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "Private subnet IDs"
  value       = aws_subnet.private[*].id
}
EOF
    
    success "Terraform configuration generated"
}

generate_ecs_config() {
    log "Generating ECS configuration..."
    
    cat > ${TERRAFORM_DIR}/ecs.tf << EOF
# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "\${var.project_name}-\${var.environment}"
  
  setting {
    name  = "containerInsights"
    value = "enabled"
  }
}

# ECS Task Definition
resource "aws_ecs_task_definition" "app" {
  family                   = "\${var.project_name}-\${var.environment}"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"
  memory                   = "512"
  execution_role_arn       = aws_iam_role.ecs_execution.arn
  
  container_definitions = jsonencode([
    {
      name      = "app"
      image     = "nginx:latest" # Placeholder - will be updated during deployment
      essential = true
      
      portMappings = [
        {
          containerPort = 3000
          protocol      = "tcp"
        }
      ]
      
      logConfiguration = {
        logDriver = "awslogs"
        options = {
          awslogs-group         = aws_cloudwatch_log_group.app.name
          awslogs-region        = var.aws_region
          awslogs-stream-prefix = "ecs"
        }
      }
      
      environment = [
        {
          name  = "NODE_ENV"
          value = var.environment
        }
      ]
    }
  ])
}

# ECS Service
resource "aws_ecs_service" "app" {
  name            = "\${var.project_name}-\${var.environment}"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.app.arn
  desired_count   = 1
  launch_type     = "FARGATE"
  
  network_configuration {
    subnets         = aws_subnet.private[*].id
    security_groups = [aws_security_group.ecs.id]
  }
  
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "app"
    container_port   = 3000
  }
  
  depends_on = [aws_lb_listener.app]
}

# Security Group for ECS
resource "aws_security_group" "ecs" {
  name_prefix = "\${var.project_name}-\${var.environment}-ecs"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 3000
    to_port         = 3000
    protocol        = "tcp"
    security_groups = [aws_security_group.alb.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# IAM Role for ECS Execution
resource "aws_iam_role" "ecs_execution" {
  name = "\${var.project_name}-\${var.environment}-ecs-execution"
  
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "ecs-tasks.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/\${var.project_name}-\${var.environment}"
  retention_in_days = 7
}
EOF

    # Add ALB configuration
    cat > ${TERRAFORM_DIR}/alb.tf << EOF
# Application Load Balancer
resource "aws_lb" "main" {
  name               = "\${var.project_name}-\${var.environment}"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets           = aws_subnet.public[*].id
}

# ALB Target Group
resource "aws_lb_target_group" "app" {
  name     = "\${var.project_name}-\${var.environment}"
  port     = 3000
  protocol = "HTTP"
  vpc_id   = aws_vpc.main.id
  target_type = "ip"
  
  health_check {
    enabled             = true
    healthy_threshold   = 2
    unhealthy_threshold = 2
    timeout             = 5
    interval            = 30
    path                = "/"
    matcher             = "200"
  }
}

# ALB Listener
resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"
  
  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }
}

# Security Group for ALB
resource "aws_security_group" "alb" {
  name_prefix = "\${var.project_name}-\${var.environment}-alb"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}
EOF

    # Add ALB outputs
    cat >> ${TERRAFORM_DIR}/outputs.tf << EOF

output "load_balancer_dns" {
  description = "Load balancer DNS name"
  value       = aws_lb.main.dns_name
}

output "load_balancer_url" {
  description = "Load balancer URL"
  value       = "http://\${aws_lb.main.dns_name}"
}
EOF
}

generate_database_config() {
    local db_engine=$1
    log "Generating database configuration for $db_engine..."
    
    cat > ${TERRAFORM_DIR}/database.tf << EOF
# Database Subnet Group
resource "aws_db_subnet_group" "main" {
  count = var.enable_database ? 1 : 0
  
  name       = "\${var.project_name}-\${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-db-subnet-group"
  }
}

# Database Security Group
resource "aws_security_group" "database" {
  count = var.enable_database ? 1 : 0
  
  name_prefix = "\${var.project_name}-\${var.environment}-db"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 5432 # PostgreSQL default
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# RDS Instance
resource "aws_db_instance" "main" {
  count = var.enable_database ? 1 : 0
  
  identifier     = "\${var.project_name}-\${var.environment}-db"
  engine         = var.database_engine
  engine_version = "$([ "$db_engine" = "postgresql" ] && echo "15.4" || echo "8.0")"
  instance_class = "db.t3.micro"
  
  allocated_storage     = 20
  max_allocated_storage = 100
  storage_type          = "gp2"
  storage_encrypted     = true
  
  db_name  = replace(var.project_name, "-", "_")
  username = "dbadmin"
  password = random_password.db_password[0].result
  
  vpc_security_group_ids = [aws_security_group.database[0].id]
  db_subnet_group_name   = aws_db_subnet_group.main[0].name
  
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  skip_final_snapshot = true
  deletion_protection = false
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-database"
  }
}

# Random password for database
resource "random_password" "db_password" {
  count = var.enable_database ? 1 : 0
  
  length  = 16
  special = true
}

# Store database password in AWS Secrets Manager
resource "aws_secretsmanager_secret" "db_password" {
  count = var.enable_database ? 1 : 0
  
  name = "\${var.project_name}/\${var.environment}/database/password"
}

resource "aws_secretsmanager_secret_version" "db_password" {
  count = var.enable_database ? 1 : 0
  
  secret_id     = aws_secretsmanager_secret.db_password[0].id
  secret_string = random_password.db_password[0].result
}
EOF

    # Add database outputs
    cat >> ${TERRAFORM_DIR}/outputs.tf << EOF

output "database_endpoint" {
  description = "Database endpoint"
  value       = var.enable_database ? aws_db_instance.main[0].endpoint : null
  sensitive   = true
}

output "database_name" {
  description = "Database name"
  value       = var.enable_database ? aws_db_instance.main[0].db_name : null
}
EOF
}

generate_cache_config() {
    log "Generating Redis cache configuration..."
    
    cat > ${TERRAFORM_DIR}/cache.tf << EOF
# ElastiCache Subnet Group
resource "aws_elasticache_subnet_group" "main" {
  count = var.enable_cache ? 1 : 0
  
  name       = "\${var.project_name}-\${var.environment}-cache-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

# ElastiCache Security Group
resource "aws_security_group" "cache" {
  count = var.enable_cache ? 1 : 0
  
  name_prefix = "\${var.project_name}-\${var.environment}-cache"
  vpc_id      = aws_vpc.main.id
  
  ingress {
    from_port       = 6379
    to_port         = 6379
    protocol        = "tcp"
    security_groups = [aws_security_group.ecs.id]
  }
  
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# ElastiCache Redis Cluster
resource "aws_elasticache_replication_group" "main" {
  count = var.enable_cache ? 1 : 0
  
  replication_group_id       = "\${var.project_name}-\${var.environment}-redis"
  description                = "Redis cluster for \${var.project_name}"
  
  node_type                  = "cache.t3.micro"
  port                       = 6379
  parameter_group_name       = "default.redis7"
  
  num_cache_clusters         = 1
  
  subnet_group_name          = aws_elasticache_subnet_group.main[0].name
  security_group_ids         = [aws_security_group.cache[0].id]
  
  at_rest_encryption_enabled = true
  transit_encryption_enabled = true
  
  tags = {
    Name = "\${var.project_name}-\${var.environment}-redis"
  }
}
EOF

    # Add cache outputs
    cat >> ${TERRAFORM_DIR}/outputs.tf << EOF

output "redis_endpoint" {
  description = "Redis endpoint"
  value       = var.enable_cache ? aws_elasticache_replication_group.main[0].configuration_endpoint_address : null
}
EOF
}

# Initialize Terraform
init_terraform() {
    log "Initializing Terraform..."
    
    cd ${TERRAFORM_DIR}
    
    # Create S3 bucket for state if it doesn't exist
    aws s3 mb "s3://${PROJECT_NAME}-terraform-state" --region ${AWS_REGION} 2>/dev/null || true
    
    # Enable versioning on state bucket
    aws s3api put-bucket-versioning \
        --bucket "${PROJECT_NAME}-terraform-state" \
        --versioning-configuration Status=Enabled
    
    # Initialize Terraform
    terraform init
    
    cd ..
    success "Terraform initialized"
}

# Plan infrastructure
plan_infrastructure() {
    log "Planning infrastructure changes..."
    
    cd ${TERRAFORM_DIR}
    terraform plan -out=tfplan
    cd ..
    
    success "Infrastructure plan completed"
}

# Apply infrastructure
apply_infrastructure() {
    log "Applying infrastructure changes..."
    
    cd ${TERRAFORM_DIR}
    terraform apply tfplan
    cd ..
    
    success "Infrastructure applied successfully"
}

# Get infrastructure outputs
get_outputs() {
    log "Getting infrastructure outputs..."
    
    cd ${TERRAFORM_DIR}
    terraform output -json > ../infrastructure-outputs.json
    cd ..
    
    success "Infrastructure outputs saved to infrastructure-outputs.json"
}

# Main execution
main() {
    log "Starting infrastructure provisioning for ${PROJECT_NAME} (${ENVIRONMENT})"
    
    check_prerequisites
    generate_terraform_config
    init_terraform
    plan_infrastructure
    
    # Ask for confirmation before applying
    echo
    read -p "Do you want to apply these infrastructure changes? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        apply_infrastructure
        get_outputs
        
        success "Infrastructure provisioning completed!"
        log "Next steps:"
        log "1. Build and deploy your application"
        log "2. Configure environment variables"
        log "3. Set up monitoring and alerts"
    else
        warn "Infrastructure apply cancelled"
    fi
}

# Script execution
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi
