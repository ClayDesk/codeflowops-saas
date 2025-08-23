/**
 * Terraform Configuration
 * Centralized Terraform settings and templates management
 */

const path = require('path');
const fs = require('fs').promises;

class TerraformConfig {
  constructor() {
    this.terraformPath = process.env.TERRAFORM_PATH || '/usr/local/bin/terraform';
    this.workspaceRoot = process.env.TERRAFORM_WORKSPACE_ROOT || path.join(__dirname, '../../../temp/terraform');
    this.modulesPath = path.join(__dirname, '../terraform/modules');
    this.templatesPath = path.join(__dirname, '../terraform/templates');
    
    this.defaultConfig = {
      requiredVersion: '>= 1.0',
      awsProviderVersion: '~> 5.0',
      timeouts: {
        create: '20m',
        update: '20m',
        delete: '20m'
      }
    };
  }

  // Get default Terraform configuration
  getDefaultTerraformConfig() {
    return {
      terraform: {
        required_version: this.defaultConfig.requiredVersion,
        required_providers: {
          aws: {
            source: 'hashicorp/aws',
            version: this.defaultConfig.awsProviderVersion
          }
        }
      }
    };
  }

  // Get provider configuration
  getProviderConfig(region = 'us-east-1') {
    return {
      provider: {
        aws: {
          region: region,
          default_tags: {
            tags: {
              ManagedBy: 'CodeFlowOps',
              Environment: 'production',
              Project: '${var.project_name}',
              SessionId: '${var.session_id}'
            }
          }
        }
      }
    };
  }

  // Static site stack configuration
  getStaticSiteConfig() {
    return {
      supportedRegions: [
        'us-east-1', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-central-1', 'ap-southeast-1'
      ],
      defaultPriceClass: 'PriceClass_100',
      cacheBehaviors: {
        defaultTTL: 86400,
        maxTTL: 31536000,
        minTTL: 0,
        compress: true
      },
      customErrorPages: [
        { errorCode: 404, responseCode: 200, responsePage: '/index.html' },
        { errorCode: 403, responseCode: 200, responsePage: '/index.html' }
      ]
    };
  }

  // React app stack configuration
  getReactAppConfig() {
    return {
      supportedRegions: [
        'us-east-1', 'us-west-1', 'us-west-2',
        'eu-west-1', 'eu-central-1', 'ap-southeast-1'
      ],
      defaultPriceClass: 'PriceClass_100',
      codeBuild: {
        computeType: 'BUILD_GENERAL1_SMALL',
        image: 'aws/codebuild/amazonlinux2-x86_64-standard:3.0',
        type: 'LINUX_CONTAINER',
        timeoutInMinutes: 60,
        privilegedMode: false
      },
      cacheBehaviors: {
        defaultTTL: 86400,
        maxTTL: 31536000,
        minTTL: 0,
        compress: true,
        staticAssetsTTL: 31536000 // 1 year for static assets
      },
      spaSupport: {
        customErrorPages: [
          { errorCode: 404, responseCode: 200, responsePage: '/index.html' },
          { errorCode: 403, responseCode: 200, responsePage: '/index.html' }
        ]
      }
    };
  }

  // Generate buildspec.yml for React projects
  generateBuildSpec(buildCommand = 'npm run build', outputDir = 'build') {
    return `version: 0.2

phases:
  install:
    runtime-versions:
      nodejs: 16
    commands:
      - echo Entered the install phase...
      - npm install
  pre_build:
    commands:
      - echo Entered the pre_build phase...
      - echo Build started on \`date\`
  build:
    commands:
      - echo Entered the build phase...
      - ${buildCommand}
  post_build:
    commands:
      - echo Entered the post_build phase...
      - echo Build completed on \`date\`
      - aws s3 sync ${outputDir}/ s3://\$S3_BUCKET --delete
      - aws cloudfront create-invalidation --distribution-id \$CLOUDFRONT_DISTRIBUTION_ID --paths "/*"

artifacts:
  files:
    - '**/*'
  base-directory: '${outputDir}'
  name: \$(date +%Y-%m-%d)
`;
  }

  // Get Terraform variable definitions
  getTerraformVariables(stackType) {
    const commonVariables = {
      project_name: {
        description: 'Name of the project',
        type: 'string',
        validation: {
          condition: 'can(regex("^[a-zA-Z0-9-]+$", var.project_name))',
          error_message: 'Project name must contain only letters, numbers, and hyphens.'
        }
      },
      environment: {
        description: 'Environment (dev, staging, prod)',
        type: 'string',
        default: 'prod',
        validation: {
          condition: 'contains(["dev", "staging", "prod"], var.environment)',
          error_message: 'Environment must be dev, staging, or prod.'
        }
      },
      session_id: {
        description: 'Unique session ID for tracking',
        type: 'string'
      },
      bucket_name: {
        description: 'S3 bucket name',
        type: 'string'
      },
      aws_region: {
        description: 'AWS region',
        type: 'string',
        default: 'us-east-1'
      },
      cloudfront_price_class: {
        description: 'CloudFront price class',
        type: 'string',
        default: 'PriceClass_100',
        validation: {
          condition: 'contains(["PriceClass_All", "PriceClass_200", "PriceClass_100"], var.cloudfront_price_class)',
          error_message: 'CloudFront price class must be PriceClass_All, PriceClass_200, or PriceClass_100.'
        }
      }
    };

    if (stackType === 'react-app') {
      return {
        ...commonVariables,
        build_command: {
          description: 'Build command for React app',
          type: 'string',
          default: 'npm run build'
        },
        build_output_dir: {
          description: 'Build output directory',
          type: 'string',
          default: 'build'
        },
        node_version: {
          description: 'Node.js version for CodeBuild',
          type: 'string',
          default: '16'
        },
        github_repo_url: {
          description: 'GitHub repository URL',
          type: 'string',
          default: ''
        }
      };
    }

    return commonVariables;
  }

  // Get Terraform outputs
  getTerraformOutputs(stackType) {
    const commonOutputs = {
      site_url: {
        description: 'Live site URL',
        value: '${module.' + stackType.replace('-', '_') + '.site_url}'
      },
      s3_bucket_name: {
        description: 'S3 bucket name',
        value: '${module.' + stackType.replace('-', '_') + '.s3_bucket_name}'
      },
      cloudfront_distribution_id: {
        description: 'CloudFront distribution ID',
        value: '${module.' + stackType.replace('-', '_') + '.cloudfront_distribution_id}'
      },
      cloudfront_domain_name: {
        description: 'CloudFront domain name',
        value: '${module.' + stackType.replace('-', '_') + '.cloudfront_domain_name}'
      }
    };

    if (stackType === 'react-app') {
      return {
        ...commonOutputs,
        codebuild_project_name: {
          description: 'CodeBuild project name',
          value: '${module.react_app.codebuild_project_name}'
        },
        artifacts_bucket_name: {
          description: 'CodeBuild artifacts bucket name',
          value: '${module.react_app.artifacts_bucket_name}'
        }
      };
    }

    return commonOutputs;
  }

  // Get workspace path for session
  getSessionWorkspacePath(sessionId) {
    return path.join(this.workspaceRoot, sessionId);
  }

  // Validate Terraform installation
  async validateTerraformInstall() {
    try {
      const { spawn } = require('child_process');
      return new Promise((resolve, reject) => {
        const terraform = spawn('terraform', ['version'], { stdio: 'pipe' });
        
        let output = '';
        terraform.stdout.on('data', (data) => {
          output += data.toString();
        });
        
        terraform.on('close', (code) => {
          if (code === 0) {
            const version = output.match(/Terraform v(\d+\.\d+\.\d+)/);
            resolve({
              installed: true,
              version: version ? version[1] : 'unknown',
              path: this.terraformPath
            });
          } else {
            reject(new Error('Terraform not found or not working'));
          }
        });
      });
    } catch (error) {
      throw new Error(`Terraform validation failed: ${error.message}`);
    }
  }

  // Get configuration summary
  getConfigSummary() {
    return {
      terraformPath: this.terraformPath,
      workspaceRoot: this.workspaceRoot,
      modulesPath: this.modulesPath,
      templatesPath: this.templatesPath,
      defaultConfig: this.defaultConfig,
      supportedStacks: ['static-site', 'react-app']
    };
  }
}

module.exports = new TerraformConfig();
