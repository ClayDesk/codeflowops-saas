/**
 * Authentication Middleware
 * Handles session validation and user authentication
 */

const jwt = require('jsonwebtoken');

class AuthMiddleware {
  // Validate session ID
  static validateSession(req, res, next) {
    const sessionId = req.headers['x-session-id'] || req.body.sessionId || req.query.sessionId;
    
    if (!sessionId) {
      return res.status(400).json({
        error: 'Session ID required',
        message: 'All requests must include a valid session ID'
      });
    }

    // Validate session ID format
    if (!sessionId.match(/^sess_[a-f0-9]{8}-[a-f0-9]{4}-4[a-f0-9]{3}-[89aAbB][a-f0-9]{3}-[a-f0-9]{12}$/)) {
      return res.status(400).json({
        error: 'Invalid session ID format',
        message: 'Session ID must be a valid UUID format'
      });
    }

    req.sessionId = sessionId;
    next();
  }

  // Rate limiting per session
  static rateLimitPerSession(requestsPerMinute = 60) {
    const sessions = new Map();
    
    return (req, res, next) => {
      const sessionId = req.sessionId;
      const now = Date.now();
      const windowStart = now - 60000; // 1 minute window
      
      if (!sessions.has(sessionId)) {
        sessions.set(sessionId, []);
      }
      
      const sessionRequests = sessions.get(sessionId);
      
      // Remove old requests outside the window
      const validRequests = sessionRequests.filter(timestamp => timestamp > windowStart);
      
      if (validRequests.length >= requestsPerMinute) {
        return res.status(429).json({
          error: 'Rate limit exceeded',
          message: `Maximum ${requestsPerMinute} requests per minute per session`
        });
      }
      
      validRequests.push(now);
      sessions.set(sessionId, validRequests);
      
      next();
    };
  }

  // Validate GitHub URL
  static validateGitHubUrl(req, res, next) {
    const { githubUrl } = req.body;
    
    if (!githubUrl) {
      return res.status(400).json({
        error: 'GitHub URL required',
        message: 'A valid GitHub repository URL is required'
      });
    }

    const githubUrlPattern = /^https:\/\/github\.com\/[a-zA-Z0-9_.-]+\/[a-zA-Z0-9_.-]+\/?$/;
    
    if (!githubUrlPattern.test(githubUrl)) {
      return res.status(400).json({
        error: 'Invalid GitHub URL',
        message: 'Please provide a valid GitHub repository URL (e.g., https://github.com/username/repo)'
      });
    }

    next();
  }

  // Validate project name
  static validateProjectName(req, res, next) {
    const { projectName } = req.body;
    
    if (projectName) {
      const projectNamePattern = /^[a-zA-Z0-9-]+$/;
      
      if (!projectNamePattern.test(projectName) || projectName.length > 50) {
        return res.status(400).json({
          error: 'Invalid project name',
          message: 'Project name must contain only letters, numbers, and hyphens, and be less than 50 characters'
        });
      }
    }

    next();
  }

  // Clean up expired sessions
  static cleanupSessions() {
    // This would integrate with Redis/database to clean up old sessions
    console.log('Session cleanup triggered');
  }
}

module.exports = AuthMiddleware;
