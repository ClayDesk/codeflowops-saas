/**
 * Updated API Configuration for Modular Router System
 * Connects to both legacy simple_api.py (port 8000) and new modular_api.py (port 8001)
 * Supports intelligent stack-specific deployment routing
 */

export const API_CONFIG = {
  // Backend server configuration - SINGLE API ON PORT 8000
  BASE_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  LEGACY_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000', // Same as base
  
  // Core endpoints for integrated modular SaaS workflow
  ENDPOINTS: {
    // Analysis endpoints (existing)
    ANALYZE_REPO: '/api/analyze-repo',
    
    // Credential validation (existing)
    VALIDATE_CREDENTIALS: '/api/validate-credentials',
    
    // Stack-specific deployment (NEW - modular approach integrated)
    DEPLOY_STACK: (stackType: string) => `/api/deploy/${stackType}`,
    
    // Legacy deployment (existing fallback)
    DEPLOY_LEGACY: '/api/deploy',
    
    // Status monitoring (existing)
    STATUS: (id: string) => `/api/deployment/${id}/status`,
    URL: (id: string) => `/api/deployment/${id}/url`,
    
    // Modular API specific endpoints (NEW - on same port)
    AVAILABLE_STACKS: '/api/stacks/available',
    SYSTEM_HEALTH: '/api/system/health',
    
    // Health checks (existing)
    HEALTH: '/api/health'
  }
} as const;

// Stack type mapping for deployment routing
export const STACK_TYPES = {
  STATIC: 'static',
  REACT: 'react', 
  NEXTJS: 'nextjs',
  PYTHON: 'python',
  PHP: 'php',
  ANGULAR: 'angular',
  GENERIC: 'generic'
} as const;

export type StackType = typeof STACK_TYPES[keyof typeof STACK_TYPES];

/**
 * Helper function to build full API URLs - SINGLE API SYSTEM
 */
export const buildApiUrl = (endpoint: string, params?: Record<string, string>, useModular = true) => {
  // Always use the same base URL since modular system is integrated
  const baseUrl = API_CONFIG.BASE_URL;
  const url = new URL(endpoint, baseUrl);
  
  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      url.searchParams.set(key, value);
    });
  }
  
  return url.toString();
};

/**
 * Build stack-specific deployment URL
 */
export const buildStackDeployUrl = (stackType: StackType) => {
  return buildApiUrl(API_CONFIG.ENDPOINTS.DEPLOY_STACK(stackType));
};

/**
 * Check if modular API features are available on the integrated API
 */
export const checkModularApiHealth = async (): Promise<boolean> => {
  try {
    const response = await fetch(buildApiUrl(API_CONFIG.ENDPOINTS.SYSTEM_HEALTH));
    const data = await response.json();
    return response.ok && data.modular_system === true;
  } catch {
    // If system health endpoint doesn't exist, modular features not available
    return false;
  }
};

/**
 * API Configuration with integrated modular system
 */
export class SmartApiConfig {
  private modularAvailable = false;
  
  constructor() {
    this.checkApiAvailability();
  }
  
  private async checkApiAvailability() {
    const modularAvailable = await checkModularApiHealth();
    this.modularAvailable = modularAvailable;
    
    if (!modularAvailable) {
      console.warn('⚠️ Modular features not available, using legacy endpoints only');
    } else {
      console.info('✅ Integrated modular API system available');
    }
  }
  
  getApiUrl(endpoint: string, params?: Record<string, string>) {
    return buildApiUrl(endpoint, params);
  }
  
  isModularAvailable() {
    return this.modularAvailable;
  }
}

export const smartApiConfig = new SmartApiConfig();
