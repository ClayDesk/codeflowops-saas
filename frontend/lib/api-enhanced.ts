/**
 * Enhanced API Integration - Preserves all existing functionality
 * Adds comprehensive backend pipeline integration features
 */
import { useState, useEffect } from 'react';

// PRESERVE ALL EXISTING API FUNCTIONALITY
export interface ApiConfig {
  baseUrl: string;
  authToken: string | null;
}

export interface SmartDeployRequest {
  project_name: string;
  cloud_provider: string;
  environment: string;
  domain_name?: string;
  github_repo?: string;
  auto_deploy: boolean;
}

export interface SmartDeployResponse {
  deployment_id: string;
  status: string;
  message: string;
  created_at: string;
}

export interface DeploymentStatus {
  deployment_id: string;
  status: 'pending' | 'analyzing' | 'deploying' | 'completed' | 'failed';
  message: string;
  progress: number;
  deployment_url?: string;
  infrastructure_outputs?: Record<string, any>;
  error_details?: string;
  url_verified?: boolean;
  created_at: string;
  completed_at?: string;
}

// ENHANCED INTERFACES - ADDITIVE ONLY
export interface PipelineOrchestrationStatus {
  pipeline_id: string;
  orchestrator_status: 'initializing' | 'analyzing' | 'provisioning' | 'deploying' | 'verifying' | 'complete';
  blue_green_enabled: boolean;
  multi_tenant_mode: boolean;
  current_phase: number;
  total_phases: number;
  enhanced_features: {
    cost_optimization: boolean;
    auto_scaling: boolean;
    monitoring_enabled: boolean;
    backup_strategy: string;
  };
}

export interface MultiTenantDeployment {
  tenant_id: string;
  tenant_name: string;
  environment: string;
  deployments: DeploymentStatus[];
  resources: {
    cpu_usage: number;
    memory_usage: number;
    cost_current: number;
    cost_projected: number;
  };
}

// PRESERVE EXISTING API CONFIG HOOK
export const useApiConfig = () => {
  const [config, setConfig] = useState<ApiConfig>({
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com',
    authToken: null
  });

  useEffect(() => {
    // Load auth token from localStorage
    const token = localStorage.getItem('auth_token');
    setConfig(prev => ({ ...prev, authToken: token }));
  }, []);

  return config;
};

// PRESERVE EXISTING SMART DEPLOY API HOOK
export const useSmartDeployApi = () => {
  const config = useApiConfig();

  const smartDeploy = async (request: SmartDeployRequest): Promise<SmartDeployResponse> => {
    const response = await fetch(`${config.baseUrl}/api/smart-deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`Deployment failed: ${response.statusText}`);
    }

    return response.json();
  };

  const checkStatus = async (deploymentId: string): Promise<DeploymentStatus> => {
    const response = await fetch(`${config.baseUrl}/api/deployment/${deploymentId}/status`, {
      headers: {
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Status check failed: ${response.statusText}`);
    }

    return response.json();
  };

  return { smartDeploy, checkStatus };
};

// ENHANCED API HOOKS - ADDITIVE FUNCTIONALITY
const useComprehensivePipelineApi = () => {
  const config = useApiConfig();

  const startPipelineOrchestration = async (
    deploymentId: string,
    options: {
      enable_blue_green?: boolean;
      multi_tenant_mode?: boolean;
      cost_optimization?: boolean;
    }
  ): Promise<PipelineOrchestrationStatus> => {
    const response = await fetch(`${config.baseUrl}/api/pipeline/orchestrate`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
      body: JSON.stringify({ deployment_id: deploymentId, ...options }),
    });

    if (!response.ok) {
      throw new Error(`Pipeline orchestration failed: ${response.statusText}`);
    }

    return response.json();
  };

  const getPipelineStatus = async (pipelineId: string): Promise<PipelineOrchestrationStatus> => {
    const response = await fetch(`${config.baseUrl}/api/pipeline/${pipelineId}/status`, {
      headers: {
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Pipeline status check failed: ${response.statusText}`);
    }

    return response.json();
  };

  const enableBlueGreenDeployment = async (
    deploymentId: string
  ): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${config.baseUrl}/api/pipeline/${deploymentId}/blue-green`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
      body: JSON.stringify({ enabled: true }),
    });

    if (!response.ok) {
      throw new Error(`Blue-green enablement failed: ${response.statusText}`);
    }

    return response.json();
  };

  return {
    startPipelineOrchestration,
    getPipelineStatus,
    enableBlueGreenDeployment,
  };
};

const useMultiTenantApi = () => {
  const config = useApiConfig();

  const getTenantOverview = async (): Promise<MultiTenantDeployment[]> => {
    const response = await fetch(`${config.baseUrl}/api/multi-tenant/overview`, {
      headers: {
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Multi-tenant overview failed: ${response.statusText}`);
    }

    const data = await response.json();
    return data.tenants || [];
  };

  const getTenantDetails = async (tenantId: string): Promise<MultiTenantDeployment> => {
    const response = await fetch(`${config.baseUrl}/api/multi-tenant/${tenantId}`, {
      headers: {
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Tenant details failed: ${response.statusText}`);
    }

    return response.json();
  };

  const deployToMultipleEnvironments = async (
    request: SmartDeployRequest,
    environments: string[]
  ): Promise<{ deployments: SmartDeployResponse[] }> => {
    const response = await fetch(`${config.baseUrl}/api/multi-tenant/deploy`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
      body: JSON.stringify({
        deployment_request: request,
        target_environments: environments,
      }),
    });

    if (!response.ok) {
      throw new Error(`Multi-environment deployment failed: ${response.statusText}`);
    }

    return response.json();
  };

  return {
    getTenantOverview,
    getTenantDetails,
    deployToMultipleEnvironments,
  };
};

// ENHANCED REAL-TIME INTEGRATION - PRESERVES EXISTING WEBSOCKET FUNCTIONALITY
const useEnhancedRealTimeUpdates = (deploymentId: string) => {
  const [pipelineStatus, setPipelineStatus] = useState<PipelineOrchestrationStatus | null>(null);
  const [deploymentStatus, setDeploymentStatus] = useState<DeploymentStatus | null>(null);
  const [orchestrationLogs, setOrchestrationLogs] = useState<string[]>([]);

  useEffect(() => {
    if (!deploymentId) return;

    const config = useApiConfig();
    
    // Enhanced WebSocket connection with comprehensive pipeline integration
    const ws = new WebSocket(`${config.baseUrl.replace('http', 'ws')}/ws/enhanced-pipeline/${deploymentId}`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      switch (update.type) {
        case 'deployment_status':
          setDeploymentStatus(update.data);
          break;
        case 'pipeline_status':
          setPipelineStatus(update.data);
          break;
        case 'orchestration_log':
          setOrchestrationLogs(prev => [...prev, update.data.message]);
          break;
        case 'comprehensive_update':
          // Handle comprehensive pipeline system updates
          if (update.data.deployment_status) {
            setDeploymentStatus(update.data.deployment_status);
          }
          if (update.data.pipeline_status) {
            setPipelineStatus(update.data.pipeline_status);
          }
          break;
      }
    };

    ws.onopen = () => {
      console.log('Enhanced real-time connection established');
    };

    ws.onerror = (error) => {
      console.error('Enhanced WebSocket error:', error);
    };

    return () => {
      ws.close();
    };
  }, [deploymentId]);

  return {
    pipelineStatus,
    deploymentStatus,
    orchestrationLogs,
  };
};

// ANALYTICS AND METRICS - NEW FUNCTIONALITY
const usePipelineAnalytics = () => {
  const config = useApiConfig();

  const getDeploymentMetrics = async (timeRange: '24h' | '7d' | '30d' = '24h') => {
    const response = await fetch(`${config.baseUrl}/api/analytics/deployments?range=${timeRange}`, {
      headers: {
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Analytics fetch failed: ${response.statusText}`);
    }

    return response.json();
  };

  const getCostOptimizationReport = async () => {
    const response = await fetch(`${config.baseUrl}/api/analytics/cost-optimization`, {
      headers: {
        ...(config.authToken && { 'Authorization': `Bearer ${config.authToken}` }),
      },
    });

    if (!response.ok) {
      throw new Error(`Cost optimization report failed: ${response.statusText}`);
    }

    return response.json();
  };

  return {
    getDeploymentMetrics,
    getCostOptimizationReport,
  };
};

// PRESERVE ALL EXISTING EXPORTS
export {
  // Existing functionality preserved
  useApiConfig as useOriginalApiConfig,
  useSmartDeployApi as useOriginalSmartDeployApi,
};

// ENHANCED EXPORTS - ADDITIVE FUNCTIONALITY
export {
  useComprehensivePipelineApi,
  useMultiTenantApi,
  useEnhancedRealTimeUpdates,
  usePipelineAnalytics,
};
