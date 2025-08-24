/**
 * TerraformGenerator.js - Modular Terraform stack generation
 */

const fs = require('fs').promises;
const path = require('path');
const { v4: uuidv4 } = require('uuid');

class TerraformGenerator {
  constructor() {
    this.templatesPath = path.join(__dirname, '../terraform/modules');
    this.outputPath = path.join(__dirname, '../../../temp/terraform');
  }

  async generateStack(stackType, projectConfig, sessionId) {
    console.log(`[${sessionId}] Generating ${stackType} Terraform stack...`);
    
    const stackConfig = {
      sessionId,
      projectName: this.sanitizeProjectName(projectConfig.name || `project-${sessionId.slice(0, 8)}`),
      stackType,
      bucketName: this.generateBucketName(projectConfig.name, sessionId),
      region: projectConfig.region || 'us-east-1',
      environment: 'prod',
      timestamp: new Date().toISOString()
    };

    try {
      // Create session-specific directory
      const sessionDir = path.join(this.outputPath, sessionId);
      await fs.mkdir(sessionDir, { recursive: true });

      let terraformConfig;
      
      switch (stackType) {
        case 'static-site':
          terraformConfig = await this.generateStaticSiteStack(stackConfig, projectConfig);
          break;
        case 'react-app':
          terraformConfig = await this.generateReactAppStack(stackConfig, projectConfig);
          break;
        default:
          throw new Error(`Unsupported stack type: ${stackType}`);
      }

      // Write Terraform files
      await this.writeTerraformFiles(sessionDir, terraformConfig);
      
      // Generate terraform.tfvars
      await this.generateTfVars(sessionDir, stackConfig, projectConfig);
      
      console.log(`[${sessionId}] Terraform stack generated successfully`);
      
      return {
        sessionId,
        stackType,
        terraformPath: sessionDir,
        config: stackConfig,
        files: terraformConfig.files
      };
      
    } catch (error) {
      console.error(`[${sessionId}] Terraform generation failed:`, error.message);
      throw error;
    }
  }

  async generateStaticSiteStack(stackConfig, projectConfig) {
    const mainTf = `
# Static Site Infrastructure
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
}

module "static_site" {
  source = "./modules/static-site"

  project_name           = var.project_name
  environment           = var.environment
  session_id            = var.session_id
  bucket_name           = var.bucket_name
  cloudfront_price_class = var.cloudfront_price_class
  aws_region            = var.aws_region
}

# Outputs
output "site_url" {
  description = "Live site URL"
  value       = module.static_site.site_url
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.static_site.s3_bucket_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.static_site.cloudfront_distribution_id
}
`;

    const variablesTf = `
variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "prod"
}

variable "session_id" {
  description = "Session ID"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}
`;

    return {
      files: {
        'main.tf': mainTf,
        'variables.tf': variablesTf
      },
      modules: ['static-site']
    };
  }

  async generateReactAppStack(stackConfig, projectConfig) {
    const mainTf = `
# React App Infrastructure
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
}

module "react_app" {
  source = "./modules/react-app"

  project_name           = var.project_name
  environment           = var.environment
  session_id            = var.session_id
  bucket_name           = var.bucket_name
  cloudfront_price_class = var.cloudfront_price_class
  aws_region            = var.aws_region
  build_command         = var.build_command
  build_output_dir      = var.build_output_dir
  node_version          = var.node_version
  github_repo_url       = var.github_repo_url
}

# Outputs
output "site_url" {
  description = "Live site URL"
  value       = module.react_app.site_url
}

output "s3_bucket_name" {
  description = "S3 bucket name"
  value       = module.react_app.s3_bucket_name
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.react_app.cloudfront_distribution_id
}

output "codebuild_project_name" {
  description = "CodeBuild project name"
  value       = module.react_app.codebuild_project_name
}
`;

    const variablesTf = `
variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Environment"
  type        = string
  default     = "prod"
}

variable "session_id" {
  description = "Session ID"
  type        = string
}

variable "bucket_name" {
  description = "S3 bucket name"
  type        = string
}

variable "cloudfront_price_class" {
  description = "CloudFront price class"
  type        = string
  default     = "PriceClass_100"
}

variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "build_command" {
  description = "Build command for React app"
  type        = string
  default     = "npm run build"
}

variable "build_output_dir" {
  description = "Build output directory"
  type        = string
  default     = "build"
}

variable "node_version" {
  description = "Node.js version"
  type        = string
  default     = "16"
}

variable "github_repo_url" {
  description = "GitHub repository URL"
  type        = string
  default     = ""
}
`;

    return {
      files: {
        'main.tf': mainTf,
        'variables.tf': variablesTf
      },
      modules: ['react-app']
    };
  }

  async writeTerraformFiles(sessionDir, terraformConfig) {
    // Write main Terraform files
    for (const [filename, content] of Object.entries(terraformConfig.files)) {
      await fs.writeFile(path.join(sessionDir, filename), content);
    }

    // Copy module files
    for (const moduleName of terraformConfig.modules) {
      const moduleSourcePath = path.join(this.templatesPath, moduleName);
      const moduleDestPath = path.join(sessionDir, 'modules', moduleName);
      
      await fs.mkdir(moduleDestPath, { recursive: true });
      await this.copyDirectory(moduleSourcePath, moduleDestPath);
    }
  }

  async generateTfVars(sessionDir, stackConfig, projectConfig) {
    const tfVars = `
# Auto-generated terraform.tfvars
project_name            = "${stackConfig.projectName}"
environment            = "${stackConfig.environment}"
session_id             = "${stackConfig.sessionId}"
bucket_name            = "${stackConfig.bucketName}"
cloudfront_price_class = "PriceClass_100"
aws_region             = "${stackConfig.region}"
${stackConfig.stackType === 'react-app' ? `
build_command          = "${projectConfig.buildCommand || 'npm run build'}"
build_output_dir       = "${projectConfig.buildOutputDir || 'build'}"
node_version           = "${projectConfig.nodeVersion || '16'}"
github_repo_url        = "${projectConfig.githubUrl || ''}"
` : ''}
`;
    
    await fs.writeFile(path.join(sessionDir, 'terraform.tfvars'), tfVars.trim());
  }

  async copyDirectory(src, dest) {
    await fs.mkdir(dest, { recursive: true });
    const files = await fs.readdir(src);
    
    for (const file of files) {
      const srcPath = path.join(src, file);
      const destPath = path.join(dest, file);
      const stats = await fs.stat(srcPath);
      
      if (stats.isDirectory()) {
        await this.copyDirectory(srcPath, destPath);
      } else {
        await fs.copyFile(srcPath, destPath);
      }
    }
  }

  sanitizeProjectName(name) {
    return name
      .toLowerCase()
      .replace(/[^a-z0-9-]/g, '-')
      .replace(/-+/g, '-')
      .replace(/^-|-$/g, '')
      .substring(0, 50);
  }

  generateBucketName(projectName, sessionId) {
    const sanitizedName = this.sanitizeProjectName(projectName || 'project');
    const shortSessionId = sessionId.slice(0, 8);
    const timestamp = Date.now().toString().slice(-6);
    
    return `codeflowops-${sanitizedName}-${shortSessionId}-${timestamp}`;
  }
}

module.exports = TerraformGenerator;
