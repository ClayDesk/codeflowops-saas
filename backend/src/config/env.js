/**
 * Environment Configuration
 * Centralized environment variable management and validation
 */

const dotenv = require('dotenv');
const path = require('path');

class EnvConfig {
  constructor() {
    this.loadEnvironment();
    this.validateRequiredVars();
  }

  loadEnvironment() {
    // Load environment variables from .env file
    const envPath = path.join(__dirname, '../../../.env');
    dotenv.config({ path: envPath });

    // Set defaults for missing environment variables
    this.setDefaults();
  }

  setDefaults() {
    // Server configuration
    process.env.NODE_ENV = process.env.NODE_ENV || 'development';
    process.env.PORT = process.env.PORT || '3000';
    process.env.HOST = process.env.HOST || 'localhost';

    // AWS configuration
    process.env.AWS_REGION = process.env.AWS_REGION || 'us-east-1';
    process.env.AWS_PROFILE = process.env.AWS_PROFILE || 'default';

    // Terraform configuration
    process.env.TERRAFORM_PATH = process.env.TERRAFORM_PATH || '/usr/local/bin/terraform';
    process.env.TERRAFORM_WORKSPACE_ROOT = process.env.TERRAFORM_WORKSPACE_ROOT || 
      path.join(__dirname, '../../../temp/terraform');

    // Session configuration
    process.env.SESSION_TIMEOUT = process.env.SESSION_TIMEOUT || '3600'; // 1 hour
    process.env.MAX_CONCURRENT_SESSIONS = process.env.MAX_CONCURRENT_SESSIONS || '1000';

    // Build configuration
    process.env.BUILD_TIMEOUT = process.env.BUILD_TIMEOUT || '600'; // 10 minutes
    process.env.MAX_BUILD_SIZE = process.env.MAX_BUILD_SIZE || '100'; // 100MB

    // Rate limiting
    process.env.RATE_LIMIT_REQUESTS = process.env.RATE_LIMIT_REQUESTS || '60'; // per minute
    process.env.RATE_LIMIT_WINDOW = process.env.RATE_LIMIT_WINDOW || '60'; // seconds

    // Database configuration (if using)
    process.env.DATABASE_URL = process.env.DATABASE_URL || 'sqlite:./codeflowops.db';
    process.env.REDIS_URL = process.env.REDIS_URL || 'redis://localhost:6379';

    // Security
    process.env.JWT_SECRET = process.env.JWT_SECRET || 'codeflowops-secret-key-change-in-production';
    process.env.CORS_ORIGIN = process.env.CORS_ORIGIN || 'http://localhost:3000';

    // Logging
    process.env.LOG_LEVEL = process.env.LOG_LEVEL || 'info';
    process.env.LOG_FORMAT = process.env.LOG_FORMAT || 'combined';

    // Feature flags
    process.env.ENABLE_WEBSOCKETS = process.env.ENABLE_WEBSOCKETS || 'true';
    process.env.ENABLE_ANALYTICS = process.env.ENABLE_ANALYTICS || 'false';
    process.env.ENABLE_DEBUG_LOGS = process.env.ENABLE_DEBUG_LOGS || 'false';
  }

  validateRequiredVars() {
    const requiredVars = [];

    // Check for required AWS variables in production
    if (this.isProduction()) {
      if (!process.env.AWS_ACCESS_KEY_ID && !process.env.AWS_PROFILE) {
        requiredVars.push('AWS_ACCESS_KEY_ID or AWS_PROFILE');
      }
      if (!process.env.AWS_SECRET_ACCESS_KEY && !process.env.AWS_PROFILE) {
        requiredVars.push('AWS_SECRET_ACCESS_KEY or AWS_PROFILE');
      }
    }

    if (requiredVars.length > 0) {
      throw new Error(`Missing required environment variables: ${requiredVars.join(', ')}`);
    }
  }

  // Environment checkers
  isDevelopment() {
    return process.env.NODE_ENV === 'development';
  }

  isProduction() {
    return process.env.NODE_ENV === 'production';
  }

  isTest() {
    return process.env.NODE_ENV === 'test';
  }

  // Configuration getters
  getServerConfig() {
    return {
      port: parseInt(process.env.PORT),
      host: process.env.HOST,
      nodeEnv: process.env.NODE_ENV,
      cors: {
        origin: process.env.CORS_ORIGIN.split(','),
        credentials: true
      }
    };
  }

  getAWSConfig() {
    return {
      region: process.env.AWS_REGION,
      profile: process.env.AWS_PROFILE,
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      sessionToken: process.env.AWS_SESSION_TOKEN
    };
  }

  getTerraformConfig() {
    return {
      path: process.env.TERRAFORM_PATH,
      workspaceRoot: process.env.TERRAFORM_WORKSPACE_ROOT,
      timeout: parseInt(process.env.TERRAFORM_TIMEOUT) || 1200 // 20 minutes
    };
  }

  getSessionConfig() {
    return {
      timeout: parseInt(process.env.SESSION_TIMEOUT),
      maxConcurrent: parseInt(process.env.MAX_CONCURRENT_SESSIONS),
      cleanupInterval: parseInt(process.env.SESSION_CLEANUP_INTERVAL) || 300 // 5 minutes
    };
  }

  getBuildConfig() {
    return {
      timeout: parseInt(process.env.BUILD_TIMEOUT),
      maxSize: parseInt(process.env.MAX_BUILD_SIZE) * 1024 * 1024, // Convert MB to bytes
      allowedCommands: (process.env.ALLOWED_BUILD_COMMANDS || 'npm,yarn').split(','),
      nodeVersions: (process.env.ALLOWED_NODE_VERSIONS || '14,16,18').split(',')
    };
  }

  getRateLimitConfig() {
    return {
      requests: parseInt(process.env.RATE_LIMIT_REQUESTS),
      window: parseInt(process.env.RATE_LIMIT_WINDOW) * 1000, // Convert to milliseconds
      skipSuccessfulRequests: process.env.RATE_LIMIT_SKIP_SUCCESS === 'true'
    };
  }

  getDatabaseConfig() {
    return {
      url: process.env.DATABASE_URL,
      redisUrl: process.env.REDIS_URL,
      poolSize: parseInt(process.env.DB_POOL_SIZE) || 10,
      timeout: parseInt(process.env.DB_TIMEOUT) || 30000
    };
  }

  getSecurityConfig() {
    return {
      jwtSecret: process.env.JWT_SECRET,
      jwtExpiry: process.env.JWT_EXPIRY || '24h',
      bcryptRounds: parseInt(process.env.BCRYPT_ROUNDS) || 12,
      maxRequestSize: process.env.MAX_REQUEST_SIZE || '10mb'
    };
  }

  getLoggingConfig() {
    return {
      level: process.env.LOG_LEVEL,
      format: process.env.LOG_FORMAT,
      enableDebug: process.env.ENABLE_DEBUG_LOGS === 'true',
      logFile: process.env.LOG_FILE || './logs/codeflowops.log'
    };
  }

  getFeatureFlags() {
    return {
      websockets: process.env.ENABLE_WEBSOCKETS === 'true',
      analytics: process.env.ENABLE_ANALYTICS === 'true',
      debugLogs: process.env.ENABLE_DEBUG_LOGS === 'true',
      rateLimiting: process.env.ENABLE_RATE_LIMITING !== 'false',
      sessionCleanup: process.env.ENABLE_SESSION_CLEANUP !== 'false'
    };
  }

  // Get all configuration
  getAllConfig() {
    return {
      server: this.getServerConfig(),
      aws: this.getAWSConfig(),
      terraform: this.getTerraformConfig(),
      session: this.getSessionConfig(),
      build: this.getBuildConfig(),
      rateLimit: this.getRateLimitConfig(),
      database: this.getDatabaseConfig(),
      security: this.getSecurityConfig(),
      logging: this.getLoggingConfig(),
      features: this.getFeatureFlags()
    };
  }

  // Validate configuration
  validateConfig() {
    const errors = [];

    // Validate server config
    if (isNaN(this.getServerConfig().port)) {
      errors.push('PORT must be a valid number');
    }

    // Validate build config
    if (this.getBuildConfig().timeout < 60) {
      errors.push('BUILD_TIMEOUT must be at least 60 seconds');
    }

    // Validate rate limit config
    if (this.getRateLimitConfig().requests < 1) {
      errors.push('RATE_LIMIT_REQUESTS must be at least 1');
    }

    return {
      valid: errors.length === 0,
      errors
    };
  }
}

module.exports = new EnvConfig();
