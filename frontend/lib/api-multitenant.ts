/**
 * Multi-tenant API client with session-based credential management.
 * Handles dynamic credentials for thousands of concurrent users.
 */

import { v4 as uuidv4 } from 'uuid';

// Types for multi-tenant operations
interface UserSession {
  session_id: string;
  user_id: string;
  tenant_id: string;
  expires_at: string;
  aws_region: string;
  permissions: any;
}

interface SessionCredentialRequest {
  aws_access_key: string;
  aws_secret_key: string;
  aws_region?: string;
  session_name?: string;
  session_duration?: number;
}

interface RepositoryAnalysisRequest {
  repo_url: string;
  analysis_type: string;
  user_context: {
    user_id: string;
    tenant_id: string;
    session_id: string;
    ip_address?: string;
    user_agent?: string;
  };
}

interface DeploymentRequest {
  session_id: string;
  analysis_id: string;
  deployment_config?: any;
}

class MultiTenantApiClient {
  private baseUrl: string;
  private currentSession: UserSession | null = null;
  private userContext: any = null;

  constructor(baseUrl: string = 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.initializeUserContext();
  }

  /**
   * Initialize user context for multi-tenant operations.
   * In production, this would come from authentication.
   */
  private initializeUserContext() {
    // Generate or retrieve user context
    // In production, this comes from JWT token/authentication
    this.userContext = {
      user_id: this.getUserId(),
      tenant_id: this.getTenantId(),
      session_id: uuidv4(),
      user_agent: navigator.userAgent
    };
  }

  private getUserId(): string {
    // In production, extract from authentication
    let userId = localStorage.getItem('codeflowops_user_id');
    if (!userId) {
      userId = `user_${uuidv4()}`;
      localStorage.setItem('codeflowops_user_id', userId);
    }
    return userId;
  }

  private getTenantId(): string {
    // In production, extract from authentication/organization
    let tenantId = localStorage.getItem('codeflowops_tenant_id');
    if (!tenantId) {
      tenantId = `tenant_${uuidv4()}`;
      localStorage.setItem('codeflowops_tenant_id', tenantId);
    }
    return tenantId;
  }

  /**
   * Validate AWS credentials and create a secure session.
   * This replaces the old direct credential validation.
   */
  async validateCredentialsAndCreateSession(credentials: {
    aws_access_key_id: string;
    aws_secret_access_key: string;
    aws_region?: string;
  }): Promise<UserSession> {
    const requestPayload: SessionCredentialRequest = {
      aws_access_key: credentials.aws_access_key_id,
      aws_secret_key: credentials.aws_secret_access_key,
      aws_region: credentials.aws_region || 'us-east-1',
      session_duration: 3600 // 1 hour
    };

    const response = await fetch(`${this.baseUrl}/api/auth/validate-credentials`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-ID': this.userContext.user_id,
        'X-Tenant-ID': this.userContext.tenant_id,
        'X-Session-ID': this.userContext.session_id
      },
      body: JSON.stringify(requestPayload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to validate credentials');
    }

    const result = await response.json();
    
    if (result.success) {
      this.currentSession = {
        session_id: result.session_id,
        user_id: this.userContext.user_id,
        tenant_id: this.userContext.tenant_id,
        expires_at: result.expires_at,
        aws_region: result.aws_region,
        permissions: result.permissions
      };
      
      // Store session for persistence
      localStorage.setItem('codeflowops_session', JSON.stringify(this.currentSession));
      
      return this.currentSession;
    } else {
      throw new Error('Credential validation failed');
    }
  }

  /**
   * Restore session from local storage.
   */
  async restoreSession(): Promise<UserSession | null> {
    const sessionData = localStorage.getItem('codeflowops_session');
    if (!sessionData) return null;

    try {
      const session = JSON.parse(sessionData);
      
      // Check if session is expired
      if (new Date(session.expires_at) < new Date()) {
        localStorage.removeItem('codeflowops_session');
        return null;
      }

      // Verify session with server
      const response = await fetch(`${this.baseUrl}/api/auth/session/${session.session_id}`);
      if (response.ok) {
        this.currentSession = session;
        return session;
      } else {
        localStorage.removeItem('codeflowops_session');
        return null;
      }
    } catch (error) {
      localStorage.removeItem('codeflowops_session');
      return null;
    }
  }

  /**
   * Get current session information.
   */
  getCurrentSession(): UserSession | null {
    return this.currentSession;
  }

  /**
   * Check if user has an active session.
   */
  hasActiveSession(): boolean {
    if (!this.currentSession) return false;
    return new Date(this.currentSession.expires_at) > new Date();
  }

  /**
   * Revoke current session.
   */
  async revokeSession(): Promise<void> {
    if (!this.currentSession) return;

    try {
      await fetch(`${this.baseUrl}/api/auth/session/${this.currentSession.session_id}`, {
        method: 'DELETE'
      });
    } catch (error) {
      console.warn('Failed to revoke session on server:', error);
    }

    this.currentSession = null;
    localStorage.removeItem('codeflowops_session');
  }

  /**
   * Analyze repository with session context.
   */
  async analyzeRepository(repo_url: string, analysis_type: string = 'full'): Promise<any> {
    if (!this.hasActiveSession()) {
      throw new Error('No active session. Please validate credentials first.');
    }

    const requestPayload: RepositoryAnalysisRequest = {
      repo_url,
      analysis_type,
      user_context: {
        user_id: this.currentSession!.user_id,
        tenant_id: this.currentSession!.tenant_id,
        session_id: this.currentSession!.session_id,
        user_agent: this.userContext.user_agent
      }
    };

    const response = await fetch(`${this.baseUrl}/api/analyze-repo`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestPayload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Repository analysis failed');
    }

    return response.json();
  }

  /**
   * Deploy using session credentials.
   */
  async deployWithSession(analysis_id: string, deployment_config?: any): Promise<any> {
    if (!this.hasActiveSession()) {
      throw new Error('No active session. Please validate credentials first.');
    }

    const requestPayload: DeploymentRequest = {
      session_id: this.currentSession!.session_id,
      analysis_id,
      deployment_config
    };

    const response = await fetch(`${this.baseUrl}/api/deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(requestPayload)
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Deployment failed');
    }

    return response.json();
  }

  /**
   * Get system health and statistics.
   */
  async getSystemStats(): Promise<any> {
    const response = await fetch(`${this.baseUrl}/api/system/stats`);
    return response.json();
  }

  /**
   * Get available deployment stacks.
   */
  async getAvailableStacks(): Promise<string[]> {
    const stats = await this.getSystemStats();
    return stats.available_stacks || [];
  }
}

// Create singleton instance
const multiTenantApi = new MultiTenantApiClient();

// Export both class and instance
export { MultiTenantApiClient, multiTenantApi };

// Legacy compatibility exports
export const api = {
  // Updated method with session management
  validateAwsCredentials: async (credentials: {
    aws_access_key: string;
    aws_secret_key: string;
    aws_region?: string;
  }) => {
    return multiTenantApi.validateCredentialsAndCreateSession({
      aws_access_key_id: credentials.aws_access_key,
      aws_secret_access_key: credentials.aws_secret_key,
      aws_region: credentials.aws_region
    });
  },

  // Updated method with session context
  analyzeRepository: async (repo_url: string, analysis_type: string = 'full') => {
    return multiTenantApi.analyzeRepository(repo_url, analysis_type);
  },

  // New session management methods
  getCurrentSession: () => multiTenantApi.getCurrentSession(),
  hasActiveSession: () => multiTenantApi.hasActiveSession(),
  restoreSession: () => multiTenantApi.restoreSession(),
  revokeSession: () => multiTenantApi.revokeSession(),
  
  // Deployment with session
  deployWithSession: (analysis_id: string, config?: any) => {
    return multiTenantApi.deployWithSession(analysis_id, config);
  }
};
