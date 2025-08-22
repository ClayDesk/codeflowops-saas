# Terraform and Provider Configuration for Static Site Template

terraform {
  required_version = ">= 1.0"
  
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.1"
    }
  }
}

# AWS Provider Configuration
provider "aws" {
  region = var.aws_region
  
  default_tags {
    tags = merge({
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "CodeFlowOps"
      Template    = "static_site"
      CreatedAt   = timestamp()
    }, var.tags)
  }
}

# AWS Provider for ACM (must be in us-east-1 for CloudFront)
provider "aws" {
  alias  = "us_east_1"
  region = "us-east-1"
  
  default_tags {
    tags = merge({
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "CodeFlowOps"
      Template    = "static_site"
      CreatedAt   = timestamp()
    }, var.tags)
  }
}
