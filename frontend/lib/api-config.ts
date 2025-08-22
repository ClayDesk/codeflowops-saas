/**
 * API Configuration for CodeFlowOps Simple SaaS
 * Connects to the simple_backend.py server running on port 8000
 * Just 4 core endpoints for the simplified workflow
 */

export const API_CONFIG = {
  // Backend server configuration
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  
  // Core endpoints for simple SaaS workflow
  ENDPOINTS: {
    // Step 1: Analyze GitHub repository
    ANALYZE_REPO: '/api/analyze-repo',
    
    // Step 2: Validate AWS credentials (stores in session)
    VALIDATE_CREDENTIALS: '/api/validate-credentials',
    
    // Step 3: Deploy to AWS with credentials
    DEPLOY: '/api/deploy',
    
    // Step 4: Get deployment status
    STATUS: (id: string) => `/api/deployment/${id}/status`,
    
    // Step 5: Get live URL
    URL: (id: string) => `/api/deployment/${id}/url`,
    
    // Health check
    HEALTH: '/api/health'
  }
} as const;

/**
 * Helper function to build full API URLs
 */
export const buildApiUrl = (endpoint: string, params?: Record<string, string>) => {
  const url = new URL(endpoint, API_CONFIG.BASE_URL);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.append(key, value);
    });
  }
  
  return url.toString();
};

export default API_CONFIG;
