/**
 * AWS Configuration
 * Centralized AWS settings and credentials management
 */

const AWS = require('aws-sdk');

class AWSConfig {
  constructor() {
    this.region = process.env.AWS_REGION || 'us-east-1';
    this.profile = process.env.AWS_PROFILE || 'default';
    
    this.initializeAWS();
  }

  initializeAWS() {
    // Configure AWS SDK
    AWS.config.update({
      region: this.region,
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      sessionToken: process.env.AWS_SESSION_TOKEN // For temporary credentials
    });

    // Set timeouts
    AWS.config.httpOptions = {
      timeout: 120000, // 2 minutes
      connectTimeout: 10000 // 10 seconds
    };
  }

  // Get S3 client
  getS3Client() {
    return new AWS.S3({
      apiVersion: '2006-03-01',
      region: this.region,
      params: {
        Bucket: this.getDefaultBucket()
      }
    });
  }

  // Get CloudFront client
  getCloudFrontClient() {
    return new AWS.CloudFront({
      apiVersion: '2020-05-31',
      region: 'us-east-1' // CloudFront is global but uses us-east-1
    });
  }

  // Get CodeBuild client
  getCodeBuildClient() {
    return new AWS.CodeBuild({
      apiVersion: '2016-10-06',
      region: this.region
    });
  }

  // Get IAM client
  getIAMClient() {
    return new AWS.IAM({
      apiVersion: '2010-05-08',
      region: 'us-east-1' // IAM is global but uses us-east-1
    });
  }

  // Default configurations
  getDefaultBucket() {
    return process.env.DEFAULT_S3_BUCKET || 'codeflowops-deployments';
  }

  getCloudFrontConfig() {
    return {
      priceClass: process.env.CLOUDFRONT_PRICE_CLASS || 'PriceClass_100',
      defaultTTL: parseInt(process.env.CLOUDFRONT_DEFAULT_TTL) || 86400,
      maxTTL: parseInt(process.env.CLOUDFRONT_MAX_TTL) || 31536000,
      compress: process.env.CLOUDFRONT_COMPRESS !== 'false'
    };
  }

  getCodeBuildConfig() {
    return {
      computeType: process.env.CODEBUILD_COMPUTE_TYPE || 'BUILD_GENERAL1_SMALL',
      image: process.env.CODEBUILD_IMAGE || 'aws/codebuild/amazonlinux2-x86_64-standard:3.0',
      type: process.env.CODEBUILD_TYPE || 'LINUX_CONTAINER',
      timeoutInMinutes: parseInt(process.env.CODEBUILD_TIMEOUT) || 60
    };
  }

  // Resource naming helpers
  generateResourceName(projectName, sessionId, resourceType) {
    const sanitizedProject = projectName.toLowerCase().replace(/[^a-z0-9-]/g, '-');
    const shortSessionId = sessionId.replace('sess_', '').slice(0, 8);
    const timestamp = Date.now().toString().slice(-6);
    
    return `codeflowops-${sanitizedProject}-${shortSessionId}-${resourceType}-${timestamp}`;
  }

  generateS3BucketName(projectName, sessionId) {
    return this.generateResourceName(projectName, sessionId, 'bucket');
  }

  generateCloudFrontOriginId(projectName, sessionId) {
    return this.generateResourceName(projectName, sessionId, 'origin');
  }

  generateIAMRoleName(projectName, sessionId) {
    return this.generateResourceName(projectName, sessionId, 'role');
  }

  generateCodeBuildProjectName(projectName, sessionId) {
    return this.generateResourceName(projectName, sessionId, 'build');
  }

  // Validation helpers
  validateCredentials() {
    return new Promise((resolve, reject) => {
      const sts = new AWS.STS();
      sts.getCallerIdentity({}, (err, data) => {
        if (err) {
          reject(new Error(`AWS credentials validation failed: ${err.message}`));
        } else {
          resolve({
            account: data.Account,
            arn: data.Arn,
            userId: data.UserId
          });
        }
      });
    });
  }

  async checkRegionAvailability() {
    try {
      const ec2 = new AWS.EC2({ region: this.region });
      const result = await ec2.describeRegions({ RegionNames: [this.region] }).promise();
      return result.Regions.length > 0;
    } catch (error) {
      return false;
    }
  }

  // Get current AWS configuration summary
  getConfigSummary() {
    return {
      region: this.region,
      profile: this.profile,
      defaultBucket: this.getDefaultBucket(),
      cloudFrontConfig: this.getCloudFrontConfig(),
      codeBuildConfig: this.getCodeBuildConfig(),
      credentialsConfigured: !!(process.env.AWS_ACCESS_KEY_ID || process.env.AWS_PROFILE)
    };
  }
}

module.exports = new AWSConfig();
