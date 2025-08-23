/**
 * Example configuration file for CodeFlowOps SaaS
 * Copy this file to config.js and customize as needed
 */

module.exports = {
  // Server configuration
  server: {
    port: process.env.PORT || 3000,
    host: process.env.HOST || 'localhost',
    cors: {
      origin: process.env.CORS_ORIGIN ? process.env.CORS_ORIGIN.split(',') : ['http://localhost:3000'],
      credentials: true
    }
  },

  // AWS configuration
  aws: {
    region: process.env.AWS_REGION || 'us-east-1',
    profile: process.env.AWS_PROFILE || 'default',
    credentials: {
      accessKeyId: process.env.AWS_ACCESS_KEY_ID,
      secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY,
      sessionToken: process.env.AWS_SESSION_TOKEN
    },
    s3: {
      defaultBucket: process.env.DEFAULT_S3_BUCKET || 'codeflowops-deployments',
      maxFileSize: '100MB'
    },
    cloudFront: {
      priceClass: process.env.CLOUDFRONT_PRICE_CLASS || 'PriceClass_100',
      defaultTTL: parseInt(process.env.CLOUDFRONT_DEFAULT_TTL) || 86400,
      maxTTL: parseInt(process.env.CLOUDFRONT_MAX_TTL) || 31536000,
      compress: process.env.CLOUDFRONT_COMPRESS !== 'false'
    },
    codeBuild: {
      computeType: process.env.CODEBUILD_COMPUTE_TYPE || 'BUILD_GENERAL1_SMALL',
      image: process.env.CODEBUILD_IMAGE || 'aws/codebuild/amazonlinux2-x86_64-standard:3.0',
      type: process.env.CODEBUILD_TYPE || 'LINUX_CONTAINER',
      timeoutInMinutes: parseInt(process.env.CODEBUILD_TIMEOUT) || 60
    }
  },

  // Terraform configuration
  terraform: {
    executablePath: process.env.TERRAFORM_PATH || '/usr/local/bin/terraform',
    workspaceRoot: process.env.TERRAFORM_WORKSPACE_ROOT || './temp/terraform',
    modulesPaths: {
      staticSite: './src/terraform/modules/static-site',
      reactApp: './src/terraform/modules/react-app'
    },
    timeouts: {
      init: 300,      // 5 minutes
      plan: 600,      // 10 minutes
      apply: 1200,    // 20 minutes
      destroy: 900    // 15 minutes
    }
  },

  // Session management
  session: {
    timeout: parseInt(process.env.SESSION_TIMEOUT) || 3600, // 1 hour
    maxConcurrent: parseInt(process.env.MAX_CONCURRENT_SESSIONS) || 1000,
    cleanupInterval: parseInt(process.env.SESSION_CLEANUP_INTERVAL) || 300, // 5 minutes
    storageType: 'redis' // or 'memory' for development
  },

  // Build configuration
  build: {
    timeout: parseInt(process.env.BUILD_TIMEOUT) || 600, // 10 minutes
    maxOutputSize: parseInt(process.env.MAX_BUILD_SIZE) || 100, // 100MB
    allowedCommands: ['npm run build', 'yarn build', 'npm start', 'yarn start'],
    supportedNodeVersions: ['14', '16', '18', '20'],
    workspaceCleanup: true
  },

  // Rate limiting
  rateLimit: {
    enabled: process.env.ENABLE_RATE_LIMITING !== 'false',
    windowMs: parseInt(process.env.RATE_LIMIT_WINDOW) * 1000 || 60000, // 1 minute
    max: parseInt(process.env.RATE_LIMIT_REQUESTS) || 60, // requests per window
    message: 'Too many requests from this session, please try again later.',
    standardHeaders: true,
    legacyHeaders: false
  },

  // Database configuration
  database: {
    url: process.env.DATABASE_URL || 'sqlite:./codeflowops.db',
    redis: {
      url: process.env.REDIS_URL || 'redis://localhost:6379',
      options: {
        retryDelayOnFailover: 100,
        enableReadyCheck: false,
        maxRetriesPerRequest: null
      }
    },
    pool: {
      min: 2,
      max: parseInt(process.env.DB_POOL_SIZE) || 10
    }
  },

  // Security
  security: {
    jwt: {
      secret: process.env.JWT_SECRET || 'change-this-in-production',
      expiresIn: process.env.JWT_EXPIRY || '24h'
    },
    bcrypt: {
      rounds: parseInt(process.env.BCRYPT_ROUNDS) || 12
    },
    cors: {
      origin: process.env.CORS_ORIGIN || 'http://localhost:3000',
      credentials: true
    },
    maxRequestSize: process.env.MAX_REQUEST_SIZE || '10mb'
  },

  // Logging
  logging: {
    level: process.env.LOG_LEVEL || 'info',
    format: process.env.LOG_FORMAT || 'combined',
    file: process.env.LOG_FILE || './logs/codeflowops.log',
    console: process.env.NODE_ENV !== 'production',
    enableDebug: process.env.ENABLE_DEBUG_LOGS === 'true'
  },

  // Feature flags
  features: {
    websockets: process.env.ENABLE_WEBSOCKETS !== 'false',
    analytics: process.env.ENABLE_ANALYTICS === 'true',
    sessionCleanup: process.env.ENABLE_SESSION_CLEANUP !== 'false',
    buildCaching: process.env.ENABLE_BUILD_CACHING === 'true',
    errorReporting: process.env.ENABLE_ERROR_REPORTING === 'true'
  },

  // Supported project types and their configurations
  projectTypes: {
    react: {
      detectionFiles: ['package.json', 'src/App.js', 'src/index.js'],
      requiredDependencies: ['react', 'react-dom'],
      defaultBuildCommand: 'npm run build',
      defaultOutputDir: 'build',
      stackType: 'react-app'
    },
    static: {
      detectionFiles: ['index.html', '*.html'],
      excludePatterns: ['node_modules/', 'package.json'],
      stackType: 'static-site'
    }
  },

  // Error handling
  errorHandling: {
    enableStackTrace: process.env.NODE_ENV === 'development',
    enableErrorReporting: process.env.ENABLE_ERROR_REPORTING === 'true',
    retryAttempts: 3,
    retryDelay: 1000 // milliseconds
  },

  // Monitoring and analytics
  monitoring: {
    enabled: process.env.ENABLE_ANALYTICS === 'true',
    services: {
      sentry: {
        dsn: process.env.SENTRY_DSN,
        environment: process.env.NODE_ENV
      },
      datadog: {
        apiKey: process.env.DATADOG_API_KEY
      }
    }
  }
};

/**
 * Example usage:
 * const config = require('./config.example');
 * console.log('Server will run on port:', config.server.port);
 */
