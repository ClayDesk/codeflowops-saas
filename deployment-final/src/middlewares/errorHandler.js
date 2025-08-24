/**
 * Error Handler Middleware
 * Centralized error handling for the application
 */

class ErrorHandler {
  // Global error handler
  static globalErrorHandler(err, req, res, next) {
    const sessionId = req.sessionId || 'unknown';
    
    console.error(`[${sessionId}] Error:`, {
      message: err.message,
      stack: err.stack,
      url: req.url,
      method: req.method,
      timestamp: new Date().toISOString()
    });

    // Default error response
    let statusCode = 500;
    let errorResponse = {
      error: 'Internal Server Error',
      message: 'An unexpected error occurred',
      sessionId: sessionId,
      timestamp: new Date().toISOString()
    };

    // Handle specific error types
    if (err.name === 'ValidationError') {
      statusCode = 400;
      errorResponse.error = 'Validation Error';
      errorResponse.message = err.message;
    } else if (err.name === 'UnauthorizedError') {
      statusCode = 401;
      errorResponse.error = 'Unauthorized';
      errorResponse.message = 'Authentication required';
    } else if (err.code === 'ENOENT') {
      statusCode = 404;
      errorResponse.error = 'File Not Found';
      errorResponse.message = 'The requested file or resource was not found';
    } else if (err.code === 'ECONNREFUSED') {
      statusCode = 503;
      errorResponse.error = 'Service Unavailable';
      errorResponse.message = 'Unable to connect to external service';
    } else if (err.message.includes('GitHub')) {
      statusCode = 400;
      errorResponse.error = 'GitHub Repository Error';
      errorResponse.message = err.message;
    } else if (err.message.includes('Terraform')) {
      statusCode = 500;
      errorResponse.error = 'Infrastructure Deployment Error';
      errorResponse.message = 'Failed to deploy AWS infrastructure';
    } else if (err.message.includes('Build')) {
      statusCode = 500;
      errorResponse.error = 'Build Process Error';
      errorResponse.message = 'Failed to build the application';
    }

    // Add debug info in development
    if (process.env.NODE_ENV === 'development') {
      errorResponse.stack = err.stack;
      errorResponse.details = {
        name: err.name,
        code: err.code
      };
    }

    res.status(statusCode).json(errorResponse);
  }

  // Async error wrapper
  static asyncErrorHandler(fn) {
    return (req, res, next) => {
      Promise.resolve(fn(req, res, next)).catch(next);
    };
  }

  // 404 handler
  static notFoundHandler(req, res, next) {
    const error = new Error(`Route ${req.originalUrl} not found`);
    error.statusCode = 404;
    next(error);
  }

  // Deployment specific error handler
  static deploymentErrorHandler(error, sessionId) {
    const deploymentError = {
      sessionId,
      type: 'deployment_error',
      timestamp: new Date().toISOString(),
      phase: 'unknown',
      message: error.message,
      details: {}
    };

    // Categorize deployment errors
    if (error.message.includes('terraform init')) {
      deploymentError.phase = 'terraform_init';
      deploymentError.details.suggestion = 'Check AWS credentials and Terraform configuration';
    } else if (error.message.includes('terraform plan')) {
      deploymentError.phase = 'terraform_plan';
      deploymentError.details.suggestion = 'Verify Terraform template and variables';
    } else if (error.message.includes('terraform apply')) {
      deploymentError.phase = 'terraform_apply';
      deploymentError.details.suggestion = 'Check AWS permissions and resource limits';
    } else if (error.message.includes('npm install')) {
      deploymentError.phase = 'npm_install';
      deploymentError.details.suggestion = 'Check package.json and network connectivity';
    } else if (error.message.includes('npm run build')) {
      deploymentError.phase = 'build';
      deploymentError.details.suggestion = 'Fix build errors in the React application';
    } else if (error.message.includes('S3')) {
      deploymentError.phase = 's3_upload';
      deploymentError.details.suggestion = 'Check S3 bucket permissions and connectivity';
    } else if (error.message.includes('CloudFront')) {
      deploymentError.phase = 'cloudfront_invalidation';
      deploymentError.details.suggestion = 'CloudFront invalidation failed, but deployment may still be successful';
    }

    return deploymentError;
  }

  // Cleanup error handler
  static cleanupOnError(sessionId, terraformPath) {
    return async (error) => {
      console.error(`[${sessionId}] Cleaning up after error:`, error.message);
      
      try {
        // Clean up temporary files
        if (terraformPath) {
          const fs = require('fs').promises;
          await fs.rmdir(terraformPath, { recursive: true });
          console.log(`[${sessionId}] Cleaned up Terraform files`);
        }
        
        // Additional cleanup tasks would go here
        // - Cancel any running builds
        // - Clean up S3 uploads
        // - Destroy partial infrastructure
        
      } catch (cleanupError) {
        console.error(`[${sessionId}] Cleanup failed:`, cleanupError.message);
      }
    };
  }

  // Log error for monitoring
  static logError(error, context = {}) {
    const errorLog = {
      timestamp: new Date().toISOString(),
      error: {
        name: error.name,
        message: error.message,
        stack: error.stack
      },
      context
    };

    // In production, this would send to monitoring service
    console.error('Application Error:', JSON.stringify(errorLog, null, 2));
    
    // Could integrate with services like:
    // - AWS CloudWatch
    // - Sentry
    // - DataDog
    // - etc.
  }
}

module.exports = ErrorHandler;
