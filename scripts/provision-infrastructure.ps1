# Infrastructure Provisioning Script (PowerShell)
# Creates backend stack using Terraform with dynamic configuration

param(
    [string]$ProjectName = "codeflowops",
    [string]$Environment = "staging",
    [string]$AwsRegion = "us-east-1",
    [string]$AwsAccessKeyId = "",
    [string]$AwsSecretAccessKey = "",
    [string]$AwsSessionToken = "",
    [string]$RepositoryUrl = ""
)

$ErrorActionPreference = "Stop"

# Configuration
$TERRAFORM_DIR = ".\terraform_workspace"

function Write-Log {
    param([string]$Message)
    Write-Host "[$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')] $Message" -ForegroundColor Blue
}

function Write-Success {
    param([string]$Message)
    Write-Host "✅ $Message" -ForegroundColor Green
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠️  $Message" -ForegroundColor Yellow
}

function Write-Error {
    param([string]$Message)
    Write-Host "❌ $Message" -ForegroundColor Red
    exit 1
}

# Check prerequisites
function Test-Prerequisites {
    Write-Log "Checking prerequisites..."
    
    # Check if terraform is installed
    try {
        terraform --version | Out-Null
    } catch {
        Write-Error "Terraform is not installed. Please install Terraform first."
    }
    
    # Check if Docker is running
    try {
        docker ps | Out-Null
    } catch {
        Write-Error "Docker is not running. Please start Docker first."
    }
    
    # Validate AWS credentials if provided
    if ($AwsAccessKeyId -and $AwsSecretAccessKey) {
        Write-Log "Using provided AWS credentials"
        # Set environment variables for Terraform
        $env:AWS_ACCESS_KEY_ID = $AwsAccessKeyId
        $env:AWS_SECRET_ACCESS_KEY = $AwsSecretAccessKey
        $env:AWS_DEFAULT_REGION = $AwsRegion
        
        if ($AwsSessionToken) {
            $env:AWS_SESSION_TOKEN = $AwsSessionToken
        }
        
        # Test AWS credentials
        try {
            $identity = aws sts get-caller-identity --query 'Account' --output text
            if ($LASTEXITCODE -eq 0) {
                Write-Success "AWS credentials validated for account: $identity"
            } else {
                Write-Error "Invalid AWS credentials provided"
            }
        } catch {
            Write-Error "Failed to validate AWS credentials. Please check your credentials."
        }
    } else {
        # Check if AWS CLI is configured as fallback
        try {
            aws sts get-caller-identity | Out-Null
            Write-Success "Using AWS CLI configured credentials"
        } catch {
            Write-Error "No AWS credentials provided and AWS CLI is not configured. Please provide credentials or run 'aws configure' first."
        }
    }
    
    Write-Success "All prerequisites met"
}

# Load repository analysis
function Get-RepositoryAnalysis {
    # Check if repository URL is provided as parameter
    if ($RepositoryUrl) {
        Write-Log "Using repository URL from parameter: $RepositoryUrl"
        # If we have a repo URL, we should run analysis on it
        if (!(Test-Path "scripts\analyze-repo.js")) {
            Write-Error "Repository analysis script not found. Please ensure analyze-repo.js exists."
        }
        
        Write-Log "Running repository analysis..."
        try {
            node scripts\analyze-repo.js $RepositoryUrl | Out-Null
        } catch {
            Write-Error "Failed to analyze repository: $RepositoryUrl"
        }
    }
    
    $analysisFile = "repository-analysis.json"
    if (Test-Path $analysisFile) {
        return Get-Content $analysisFile | ConvertFrom-Json
    } else {
        Write-Error "Repository analysis file not found. Please run 'node scripts/analyze-repo.js <repo-url>' first."
    }
}

# Create Terraform workspace
function New-TerraformWorkspace {
    Write-Log "Creating Terraform workspace..."
    
    if (Test-Path $TERRAFORM_DIR) {
        Remove-Item $TERRAFORM_DIR -Recurse -Force
    }
    New-Item -ItemType Directory -Path $TERRAFORM_DIR | Out-Null
    
    Write-Success "Terraform workspace created"
}

# Generate main Terraform configuration
function New-MainTerraformConfig {
    param($Analysis)
    
    Write-Log "Generating main Terraform configuration..."
    
    $mainTf = @"
terraform {
  required_version = ">= 1.0"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = {
      Environment = var.environment
      Project     = var.project_name
      ManagedBy   = "terraform"
    }
  }
}

# Data sources
data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}
"@

    Set-Content -Path "$TERRAFORM_DIR\main.tf" -Value $mainTf
    Write-Success "Main configuration generated"
}

# Generate variables file
function New-VariablesConfig {
    Write-Log "Generating variables configuration..."
    
    $variablesTf = @"
variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "$ProjectName"
}

variable "environment" {
  description = "Environment name"
  type        = string
  default     = "$Environment"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "$AwsRegion"
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"
}

variable "availability_zones_count" {
  description = "Number of availability zones"
  type        = number
  default     = 2
}
"@

    Set-Content -Path "$TERRAFORM_DIR\variables.tf" -Value $variablesTf
    Write-Success "Variables configuration generated"
}

# Generate VPC configuration (only for container deployments)
function New-VPCConfig {
    param($Analysis)
    
    # Skip VPC for serverless/static deployments
    if ($Analysis.infrastructure.compute -eq "serverless") {
        Write-Log "Skipping VPC configuration for serverless deployment"
        return
    }
    
    Write-Log "Generating VPC configuration..."
    
    $vpcTf = @"
# VPC
resource "aws_vpc" "main" {
  cidr_block           = var.vpc_cidr
  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = {
    Name = "`${var.project_name}-`${var.environment}-vpc"
  }
}

# Internet Gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = {
    Name = "`${var.project_name}-`${var.environment}-igw"
  }
}

# Public Subnets
resource "aws_subnet" "public" {
  count             = var.availability_zones_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  map_public_ip_on_launch = true

  tags = {
    Name = "`${var.project_name}-`${var.environment}-public-`${count.index + 1}"
    Type = "public"
  }
}

# Private Subnets
resource "aws_subnet" "private" {
  count             = var.availability_zones_count
  vpc_id            = aws_vpc.main.id
  cidr_block        = cidrsubnet(var.vpc_cidr, 8, count.index + 10)
  availability_zone = data.aws_availability_zones.available.names[count.index]

  tags = {
    Name = "`${var.project_name}-`${var.environment}-private-`${count.index + 1}"
    Type = "private"
  }
}

# Route Table for Public Subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "`${var.project_name}-`${var.environment}-public-rt"
  }
}

# Associate Public Subnets with Route Table
resource "aws_route_table_association" "public" {
  count          = var.availability_zones_count
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}
"@

    Set-Content -Path "$TERRAFORM_DIR\vpc.tf" -Value $vpcTf
    Write-Success "VPC configuration generated"
}

# Generate compute configuration based on analysis
function New-ComputeConfig {
    param($Analysis)
    
    if ($Analysis.infrastructure.compute -eq "serverless") {
        Write-Log "Generating serverless configuration..."
        New-ServerlessConfig -Analysis $Analysis
    } else {
        Write-Log "Generating container configuration..."
        New-ECSConfig -Analysis $Analysis
    }
}

# Generate serverless configuration
function New-ServerlessConfig {
    param($Analysis)
    
    Write-Log "Generating static site hosting configuration (S3 + CloudFront)..."
    
    $serverlessTf = @"
# S3 Bucket for static website hosting
resource "aws_s3_bucket" "static_site" {
  bucket = "`${var.project_name}-`${var.environment}-static-site"

  tags = {
    Name = "`${var.project_name}-`${var.environment}-static-site"
    Type = "StaticWebsite"
  }
}

# S3 Bucket versioning
resource "aws_s3_bucket_versioning" "static_site" {
  bucket = aws_s3_bucket.static_site.id
  versioning_configuration {
    status = "Enabled"
  }
}

# S3 Bucket public access configuration
resource "aws_s3_bucket_public_access_block" "static_site" {
  bucket = aws_s3_bucket.static_site.id

  block_public_acls       = false
  block_public_policy     = false
  ignore_public_acls      = false
  restrict_public_buckets = false
}

# S3 Bucket website configuration
resource "aws_s3_bucket_website_configuration" "static_site" {
  bucket = aws_s3_bucket.static_site.id

  index_document {
    suffix = "index.html"
  }

  error_document {
    key = "404.html"
  }
}

# S3 Bucket policy for public read access
resource "aws_s3_bucket_policy" "static_site" {
  bucket = aws_s3_bucket.static_site.id

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Sid       = "PublicReadGetObject"
        Effect    = "Allow"
        Principal = "*"
        Action    = "s3:GetObject"
        Resource  = "`${aws_s3_bucket.static_site.arn}/*"
      }
    ]
  })

  depends_on = [aws_s3_bucket_public_access_block.static_site]
}

# CloudFront Origin Access Control
resource "aws_cloudfront_origin_access_control" "static_site" {
  name                              = "`${var.project_name}-`${var.environment}-oac"
  description                       = "OAC for `${var.project_name} static site"
  origin_access_control_origin_type = "s3"
  signing_behavior                  = "always"
  signing_protocol                  = "sigv4"
}

# CloudFront Distribution for global CDN
resource "aws_cloudfront_distribution" "static_site" {
  origin {
    domain_name              = aws_s3_bucket.static_site.bucket_regional_domain_name
    origin_id                = "S3-`${aws_s3_bucket.static_site.bucket}"
    origin_access_control_id = aws_cloudfront_origin_access_control.static_site.id
  }

  enabled             = true
  is_ipv6_enabled     = true
  default_root_object = "index.html"
  comment             = "`${var.project_name} `${var.environment} static site"

  # Cache behavior for static assets
  default_cache_behavior {
    allowed_methods        = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods         = ["GET", "HEAD"]
    target_origin_id       = "S3-`${aws_s3_bucket.static_site.bucket}"
    compress               = true
    viewer_protocol_policy = "redirect-to-https"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl     = 0
    default_ttl = 3600  # 1 hour
    max_ttl     = 86400 # 24 hours
  }

  # Cache behavior for Next.js assets (longer cache)
  ordered_cache_behavior {
    path_pattern     = "/_next/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "S3-`${aws_s3_bucket.static_site.bucket}"
    compress         = true

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    min_ttl                = 0
    default_ttl            = 31536000 # 1 year
    max_ttl                = 31536000 # 1 year
    viewer_protocol_policy = "redirect-to-https"
  }

  # Price class for cost optimization
  price_class = "PriceClass_100"

  # Geographic restrictions
  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  # SSL Certificate
  viewer_certificate {
    cloudfront_default_certificate = true
  }

  # Custom error responses
  custom_error_response {
    error_code         = 404
    response_code      = 404
    response_page_path = "/404.html"
  }

  custom_error_response {
    error_code         = 403
    response_code      = 404
    response_page_path = "/404.html"
  }

  tags = {
    Name        = "`${var.project_name}-`${var.environment}-cdn"
    Environment = var.environment
  }
}

# CodeBuild project for CI/CD
resource "aws_codebuild_project" "static_site" {
  name          = "`${var.project_name}-`${var.environment}-build"
  description   = "Build project for `${var.project_name} static site"
  service_role  = aws_iam_role.codebuild.arn

  artifacts {
    type = "S3"
    location = "`${aws_s3_bucket.static_site.bucket}/builds"
  }

  environment {
    compute_type = "BUILD_GENERAL1_SMALL"
    image        = "aws/codebuild/amazonlinux2-x86_64-standard:5.0"
    type         = "LINUX_CONTAINER"

    environment_variable {
      name  = "S3_BUCKET"
      value = aws_s3_bucket.static_site.bucket
    }

    environment_variable {
      name  = "CLOUDFRONT_DISTRIBUTION_ID"
      value = aws_cloudfront_distribution.static_site.id
    }
  }

  source {
    type = "GITHUB"
    location = "$RepositoryUrl"
    
    buildspec = "buildspec.yml"
  }

  tags = {
    Name        = "`${var.project_name}-`${var.environment}-build"
    Environment = var.environment
  }
}

# CodeBuild IAM Role
resource "aws_iam_role" "codebuild" {
  name = "`${var.project_name}-`${var.environment}-codebuild-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "codebuild.amazonaws.com"
        }
      }
    ]
  })

  tags = {
    Name = "`${var.project_name}-`${var.environment}-codebuild-role"
  }
}

# CodeBuild IAM Policy
resource "aws_iam_role_policy" "codebuild" {
  role = aws_iam_role.codebuild.name

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "logs:CreateLogGroup",
          "logs:CreateLogStream",
          "logs:PutLogEvents"
        ]
        Resource = "arn:aws:logs:*:*:*"
      },
      {
        Effect = "Allow"
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject",
          "s3:ListBucket"
        ]
        Resource = [
          aws_s3_bucket.static_site.arn,
          "`${aws_s3_bucket.static_site.arn}/*"
        ]
      },
      {
        Effect = "Allow"
        Action = [
          "cloudfront:CreateInvalidation"
        ]
        Resource = aws_cloudfront_distribution.static_site.arn
      }
    ]
  })
}
"@

    Set-Content -Path "$TERRAFORM_DIR\serverless.tf" -Value $serverlessTf
    Write-Success "Static site hosting configuration generated (S3 + CloudFront + CodeBuild)"
}

# Generate ECS configuration (fallback for container deployments)
function New-ECSConfig {
    param($Analysis)
    
    Write-Log "Generating ECS configuration..."
    
    $ecsTf = @"
# ECS Cluster
resource "aws_ecs_cluster" "main" {
  name = "`${var.project_name}-`${var.environment}"

  setting {
    name  = "containerInsights"
    value = "enabled"
  }

  tags = {
    Name = "`${var.project_name}-`${var.environment}-cluster"
  }
}

# CloudWatch Log Group
resource "aws_cloudwatch_log_group" "app" {
  name              = "/ecs/`${var.project_name}-`${var.environment}"
  retention_in_days = 30

  tags = {
    Name = "`${var.project_name}-`${var.environment}-logs"
  }
}
"@

    Set-Content -Path "$TERRAFORM_DIR\ecs.tf" -Value $ecsTf
    Write-Success "ECS configuration generated"
}

# Generate IAM configuration
function New-IAMConfig {
    Write-Log "Generating IAM configuration..."
    
    $iamTf = @"
# ECS Execution Role
resource "aws_iam_role" "ecs_execution" {
  name = "`${var.project_name}-`${var.environment}-ecs-execution"

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

  tags = {
    Name = "`${var.project_name}-`${var.environment}-ecs-execution-role"
  }
}

resource "aws_iam_role_policy_attachment" "ecs_execution" {
  role       = aws_iam_role.ecs_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# ECS Task Role
resource "aws_iam_role" "ecs_task" {
  name = "`${var.project_name}-`${var.environment}-ecs-task"

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

  tags = {
    Name = "`${var.project_name}-`${var.environment}-ecs-task-role"
  }
}
"@

    Set-Content -Path "$TERRAFORM_DIR\iam.tf" -Value $iamTf
    Write-Success "IAM configuration generated"
}

# Generate Load Balancer configuration
function New-LoadBalancerConfig {
    Write-Log "Generating Load Balancer configuration..."
    
    $albTf = @"
# Security Group for ALB
resource "aws_security_group" "alb" {
  name        = "`${var.project_name}-`${var.environment}-alb"
  description = "Security group for Application Load Balancer"
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

  tags = {
    Name = "`${var.project_name}-`${var.environment}-alb-sg"
  }
}

# Application Load Balancer
resource "aws_lb" "main" {
  name               = "`${var.project_name}-`${var.environment}-alb"
  internal           = false
  load_balancer_type = "application"
  security_groups    = [aws_security_group.alb.id]
  subnets            = aws_subnet.public[*].id

  enable_deletion_protection = false

  tags = {
    Name = "`${var.project_name}-`${var.environment}-alb"
  }
}

# Target Group
resource "aws_lb_target_group" "app" {
  name        = "`${var.project_name}-`${var.environment}-tg"
  port        = 3000
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"

  health_check {
    enabled             = true
    healthy_threshold   = 2
    interval            = 30
    matcher             = "200"
    path                = "/"
    port                = "traffic-port"
    protocol            = "HTTP"
    timeout             = 5
    unhealthy_threshold = 2
  }

  tags = {
    Name = "`${var.project_name}-`${var.environment}-tg"
  }
}

# Listener
resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.main.arn
  port              = "80"
  protocol          = "HTTP"

  default_action {
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = {
    Name = "`${var.project_name}-`${var.environment}-listener"
  }
}
"@

    Set-Content -Path "$TERRAFORM_DIR\alb.tf" -Value $albTf
    Write-Success "Load Balancer configuration generated"
}

# Generate outputs
function New-OutputsConfig {
    param($Analysis)
    
    Write-Log "Generating outputs configuration..."
    
    if ($Analysis.infrastructure.compute -eq "serverless") {
        $outputsTf = @"
output "s3_bucket_name" {
  description = "Name of the S3 bucket for static site"
  value       = aws_s3_bucket.static_site.bucket
}

output "s3_website_endpoint" {
  description = "Website endpoint of the S3 bucket"
  value       = aws_s3_bucket_website_configuration.static_site.website_endpoint
}

output "cloudfront_domain_name" {
  description = "Domain name of the CloudFront distribution"
  value       = aws_cloudfront_distribution.static_site.domain_name
}

output "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution"
  value       = aws_cloudfront_distribution.static_site.id
}

output "codebuild_project_name" {
  description = "Name of the CodeBuild project"
  value       = aws_codebuild_project.static_site.name
}

output "deployment_url" {
  description = "URL where the application will be accessible"
  value       = "https://`${aws_cloudfront_distribution.static_site.domain_name}"
}
"@
    } else {
        $outputsTf = @"
output "vpc_id" {
  description = "ID of the VPC"
  value       = aws_vpc.main.id
}

output "public_subnet_ids" {
  description = "IDs of the public subnets"
  value       = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  description = "IDs of the private subnets"
  value       = aws_subnet.private[*].id
}

output "ecs_cluster_name" {
  description = "Name of the ECS cluster"
  value       = aws_ecs_cluster.main.name
}

output "alb_dns_name" {
  description = "DNS name of the load balancer"
  value       = aws_lb.main.dns_name
}

output "deployment_url" {
  description = "URL where the application will be accessible"
  value       = "http://`${aws_lb.main.dns_name}"
}
"@
    }

    Set-Content -Path "$TERRAFORM_DIR\outputs.tf" -Value $outputsTf
    Write-Success "Outputs configuration generated"
}

# Initialize and apply Terraform
function Invoke-TerraformDeploy {
    Write-Log "Initializing Terraform..."
    
    Push-Location $TERRAFORM_DIR
    try {
        # Initialize Terraform
        terraform init
        
        # Validate configuration
        Write-Log "Validating Terraform configuration..."
        terraform validate
        
        # Plan deployment
        Write-Log "Planning infrastructure deployment..."
        terraform plan -out=tfplan
        
        # Apply deployment
        Write-Log "Applying infrastructure deployment..."
        terraform apply -auto-approve tfplan
        
        # Get outputs
        Write-Log "Getting deployment outputs..."
        $outputs = terraform output -json | ConvertFrom-Json
        
        Write-Success "Infrastructure deployment completed!"
        Write-Host "`n📊 Deployment Information:" -ForegroundColor Cyan
        Write-Host "VPC ID: $($outputs.vpc_id.value)" -ForegroundColor White
        Write-Host "ECS Cluster: $($outputs.ecs_cluster_name.value)" -ForegroundColor White
        Write-Host "Load Balancer: $($outputs.alb_dns_name.value)" -ForegroundColor White
        Write-Host "Application URL: $($outputs.deployment_url.value)" -ForegroundColor Green
        
        # Save deployment info
        $deploymentInfo = @{
            timestamp = Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ"
            environment = $Environment
            framework = "FastAPI"
            buildNumber = "1.0.0"
            vpc_id = $outputs.vpc_id.value
            cluster_name = $outputs.ecs_cluster_name.value
            alb_dns = $outputs.alb_dns_name.value
            deployment_url = $outputs.deployment_url.value
        }
        
        $deploymentInfo | ConvertTo-Json -Depth 3 | Set-Content -Path "..\deployment-info.json"
        Write-Success "Deployment information saved to deployment-info.json"
        
    } finally {
        Pop-Location
    }
}

# Main execution
function main {
    Write-Log "Starting infrastructure provisioning for $ProjectName ($Environment)"
    
    Test-Prerequisites
    $analysis = Get-RepositoryAnalysis
    
    New-TerraformWorkspace
    New-MainTerraformConfig -Analysis $analysis
    New-VariablesConfig
    
    # Only create VPC for container deployments
    if ($analysis.infrastructure.compute -eq "container") {
        New-VPCConfig -Analysis $analysis
        New-LoadBalancerConfig
    }
    
    New-ComputeConfig -Analysis $analysis
    
    # Skip IAM for simple static sites
    if ($analysis.infrastructure.compute -eq "container") {
        New-IAMConfig
    }
    
    New-OutputsConfig -Analysis $analysis
    
    Invoke-TerraformDeploy
    
    Write-Success "Infrastructure provisioning completed successfully!"
    Write-Host "`n🚀 Next step: Run the deployment script to deploy your application" -ForegroundColor Cyan
}

# Run main function
main
