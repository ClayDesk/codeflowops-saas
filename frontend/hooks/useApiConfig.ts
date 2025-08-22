// Environment Configuration Hook - Dynamic API configuration (Claude removed)
'use client';

import { useState, useEffect } from 'react';

interface ApiConfig {
  baseUrl: string;
  isProduction: boolean;
  endpoints: {
    smartDeploy: string;
    deployments: string;
    websocket: string;
    integration: string;
  };
}

export const useApiConfig = () => {
  const [config, setConfig] = useState<ApiConfig>({
    baseUrl: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
    isProduction: process.env.NODE_ENV === 'production',
    endpoints: {
      smartDeploy: '/api/v1/smart-deploy',
      deployments: '/api/v1/deployments',
      websocket: '/api/v1/smart-deploy/ws/realtime',
      integration: '/api/v1/test/integration'
    }
  });

  // Claude status checking removed - using traditional Terraform templates
  // Claude status checking removed

  // Helper function to get full API URL
  const getApiUrl = (endpoint: keyof typeof config.endpoints) => {
    return `${config.baseUrl}${config.endpoints[endpoint]}`;
  };

  // Helper function to get auth headers
  const getAuthHeaders = () => {
    const token = localStorage.getItem('auth_token');
    return {
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    };
  };

  // Helper function to make authenticated API calls
  const apiCall = async (
    endpoint: keyof typeof config.endpoints, 
    path: string = '', 
    options: RequestInit = {}
  ) => {
    const url = `${getApiUrl(endpoint)}${path}`;
    const headers = {
      ...getAuthHeaders(),
      ...options.headers
    };

    return fetch(url, {
      ...options,
      headers
    });
  };

  return {
    config,
    getApiUrl,
    getAuthHeaders,
    apiCall
  };
};

// Enhanced deployment creation (Claude integration removed)
export const useEnhancedDeployment = () => {
  const { apiCall } = useApiConfig();

  const createDeployment = async (deploymentData: any) => {
    const response = await apiCall('smartDeploy', '/create', {
      method: 'POST',
      body: JSON.stringify({
        project_name: deploymentData.project_name,
        repository_url: deploymentData.github_repo,
        deployment_config: {
          cloud_provider: deploymentData.cloud_provider || 'aws',
          region: 'us-east-1',
          environment: deploymentData.environment || 'production',
          domain_name: deploymentData.domain_name || '',
          auto_deploy: deploymentData.auto_deploy || false
        }
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Deployment creation failed');
    }

    return response.json();
  };

  const getDeploymentLogs = async (deploymentId: string) => {
    const response = await apiCall('deployments', `/${deploymentId}/logs`);
    
    if (!response.ok) {
      throw new Error('Failed to fetch deployment logs');
    }
    
    return response.json();
  };

  const runIntegrationTest = async () => {
    const response = await apiCall('integration', '');
    
    if (!response.ok) {
      throw new Error('Integration test failed');
    }
    
    return response.json();
  };

  return {
    createDeployment,
    getDeploymentLogs,
    runIntegrationTest
  };
};
