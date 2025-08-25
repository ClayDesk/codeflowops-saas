import { useState, useEffect } from 'react';

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
  // Framework information for routing
  framework?: any;
  framework_type?: string;
  project_type?: string;
  analysis_result?: any;
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

// Claude integration removed - using traditional Terraform templates
// export interface ClaudeIterationData { ... }

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

  const updateAuthToken = (token: string | null) => {
    setConfig(prev => ({ ...prev, authToken: token }));
    if (token) {
      localStorage.setItem('auth_token', token);
    } else {
      localStorage.removeItem('auth_token');
    }
  };

  return {
    ...config,
    updateAuthToken
  };
};

export const useSmartDeployApi = () => {
  const { baseUrl, authToken } = useApiConfig();

  // For Smart Deploy API, use demo-token if no auth token is available
  const effectiveToken = authToken || 'demo-token';
  
  const headers = {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${effectiveToken}`
  };

  // SDK Backend Integration - Repository Analysis
  const analyzeRepository = async (repositoryUrl: string) => {
    const response = await fetch(`${baseUrl}/api/analyze-repo`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        repo_url: repositoryUrl,
        analysis_type: 'full'
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to analyze repository: ${response.statusText}`);
    }

    return response.json();
  };

  // SDK Backend Integration - Deploy with AWS Credentials
  const deployWithCredentials = async (deploymentData: {
    deployment_id: string;
    aws_access_key: string;
    aws_secret_key: string;
    aws_region?: string;
    project_name?: string;
    framework?: string;
    projectType?: string;  // Add projectType field
    detected_framework?: string;  // Add detected_framework field
    repository_url?: string;  // Add repository URL field
    repo_url?: string;  // Alternative field name
  }) => {
    console.log('🚀 deployWithCredentials called with:', {
      deployment_id: deploymentData.deployment_id,
      aws_region: deploymentData.aws_region,
      project_name: deploymentData.project_name,
      framework: deploymentData.framework,
      has_access_key: !!deploymentData.aws_access_key,
      has_secret_key: !!deploymentData.aws_secret_key
    });
    
    // Determine the correct endpoint based on framework
    const getDeploymentEndpoint = (framework?: string | any) => {
      let fw = '';
      
      // Handle framework as object (from enhanced analyzer)
      if (typeof framework === 'object' && framework?.type) {
        fw = framework.type.toLowerCase();
      } else if (typeof framework === 'string') {
        fw = framework.toLowerCase();
      }
      
      // Future framework routing can be added here
      // if (fw.includes('nextjs') || fw.includes('next.js')) {
      //   return `${baseUrl}/api/deploy/nextjs-amplify`;
      // }
      
      // Default to generic deployment (CloudFront + S3)
      return `${baseUrl}/api/deploy`;
    };
    
    // Try to get framework from multiple possible fields in deployment data
    const framework = deploymentData.framework || deploymentData.projectType || deploymentData.detected_framework;
    const endpoint = getDeploymentEndpoint(framework);
    
    console.log('🔍 ROUTING DEBUG:');
    console.log('  deploymentData.framework:', JSON.stringify(deploymentData.framework));
    console.log('  deploymentData.projectType:', deploymentData.projectType);
    console.log('  deploymentData.detected_framework:', deploymentData.detected_framework);
    console.log('  final framework used:', JSON.stringify(framework));
    console.log('  final endpoint:', endpoint);
    
    const payload = {
      analysis_id: deploymentData.deployment_id,
      aws_access_key_id: deploymentData.aws_access_key,
      aws_secret_access_key: deploymentData.aws_secret_key,
      aws_region: deploymentData.aws_region || 'us-east-1',
      project_name: deploymentData.project_name,
      repository_url: deploymentData.repository_url || deploymentData.repo_url  // Add repository URL
    };
    
    console.log('📤 Sending deploy request to:', endpoint);
    console.log('📤 Framework detected:', JSON.stringify(deploymentData.framework), '-> Endpoint:', endpoint);
    console.log('📤 Payload structure:', JSON.stringify(payload, (key, value) => {
      if (key === 'aws_access_key_id' || key === 'aws_secret_access_key') {
        return '***REDACTED***';
      }
      return value;
    }, 2));

    const response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    console.log('📥 Deploy response status:', response.status, response.statusText);
    console.log('📥 Deploy response headers:', Object.fromEntries(response.headers.entries()));

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Deploy API Error:', errorText);
      throw new Error(`Failed to deploy: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log('✅ Deploy response data:', data);
    return data;
  };

  // SDK Backend Integration - Get Deployment Status
  const getDeploymentStatusSDK = async (deploymentId: string) => {
    const response = await fetch(`${baseUrl}/api/deployment/${deploymentId}/status`, {
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`Failed to get deployment status: ${response.statusText}`);
    }

    return response.json();
  };

  // SDK Backend Integration - Get Final Deployment Result
  const getDeploymentResult = async (deploymentId: string) => {
    console.log('📊 getDeploymentResult called for:', deploymentId);
    
    const response = await fetch(`${baseUrl}/api/deployment/${deploymentId}/result`, {
      headers: { 'Content-Type': 'application/json' }
    });

    console.log('📥 Result response status:', response.status, response.statusText);

    if (!response.ok) {
      const errorText = await response.text();
      console.error('❌ Get result API Error:', errorText);
      throw new Error(`Failed to get deployment result: ${response.status} ${response.statusText} - ${errorText}`);
    }

    const data = await response.json();
    console.log('✅ Deployment result data:', data);
    return data;
  };

  // SDK Backend Integration - Validate AWS Credentials
  const validateAwsCredentials = async (credentials: {
    aws_access_key: string;
    aws_secret_key: string;
    aws_region?: string;
  }) => {
    const response = await fetch(`${baseUrl}/api/validate-credentials`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        aws_access_key: credentials.aws_access_key,
        aws_secret_key: credentials.aws_secret_key,
        aws_region: credentials.aws_region || 'us-east-1'
      })
    });

    if (!response.ok) {
      throw new Error(`Failed to validate credentials: ${response.statusText}`);
    }

    const result = await response.json();
    
    // CHECK THE ACTUAL VALIDATION RESULT - this was missing!
    if (!result.valid || result.success === false) {
      throw new Error(result.error || result.message || 'Invalid AWS credentials');
    }

    return result;
  };

  // Get Plugin System Status
  const getPluginStatus = async () => {
    const response = await fetch(`${baseUrl}/api/plugins/status`, {
      headers: { 'Content-Type': 'application/json' }
    });

    if (!response.ok) {
      throw new Error(`Failed to get plugin status: ${response.statusText}`);
    }

    return response.json();
  };

  const createDeployment = async (request: SmartDeployRequest): Promise<SmartDeployResponse> => {
    // Use framework-aware routing for deployment creation
    const getDeploymentEndpoint = (framework?: string | any) => {
      console.log('🔍 Framework detection for deployment endpoint:', framework);
      
      if (!framework) {
        console.log('⚠️ No framework provided, using default endpoint');
        return `${baseUrl}/api/deploy`;
      }
      
      // Handle framework object with type field
      const fw = typeof framework === 'object' ? framework.type : framework;
      const fwStr = String(fw).toLowerCase();
      
      console.log('🔄 Framework string for routing:', fwStr);
      
      // Default to generic deployment
      console.log('📍 Using default deployment endpoint');
      return `${baseUrl}/api/deploy`;
    };
    
    // Get the framework-specific endpoint
    const framework = request.framework || request.framework_type || request.project_type;
    const endpoint = getDeploymentEndpoint(framework);
    
    console.log('🚀 Creating deployment with framework routing:');
    console.log('  Framework data:', JSON.stringify(framework));
    console.log('  Target endpoint:', endpoint);
    console.log('  Request data:', JSON.stringify(request, null, 2));
    
    const response = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(request)
    });

    if (!response.ok) {
      throw new Error(`Failed to create deployment: ${response.statusText}`);
    }

    return response.json();
  };

  const getDeploymentStatus = async (deploymentId: string): Promise<DeploymentStatus> => {
    const response = await fetch(`${baseUrl}/api/deployment/${deploymentId}/status`, {
      headers
    });

    if (!response.ok) {
      throw new Error(`Failed to get deployment status: ${response.statusText}`);
    }

    return response.json();
  };

  const getDeploymentLogs = async (deploymentId: string) => {
    const response = await fetch(`${baseUrl}/api/v1/deployments/${deploymentId}/logs`, {
      headers
    });

    if (!response.ok) {
      throw new Error(`Failed to get deployment logs: ${response.statusText}`);
    }

    return response.json();
  };

  // Claude iterations removed - using traditional Terraform templates
  // const getClaudeIterations = async (deploymentId: string) => { ... }

  const checkHealth = async () => {
    const response = await fetch(`${baseUrl}/api/health`, {
      headers
    });
    return response.json();
  };

  return {
    // SDK Backend Integration (Primary Methods)
    analyzeRepository,
    deployWithCredentials,
    getDeploymentStatusSDK,
    getDeploymentResult,
    validateAwsCredentials,
    getPluginStatus,

    // Legacy/Compatibility Methods
    createDeployment,
    getDeploymentStatus,
    getDeploymentLogs,
    checkHealth,
  };
};

export const useWebSocket = (deploymentId: string | null) => {
  const [socket, setSocket] = useState<WebSocket | null>(null);
  const [messages, setMessages] = useState<any[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');

  useEffect(() => {
    if (!deploymentId) return;

    // WebSocket not implemented in simple backend - using polling instead
    setConnectionStatus('connected');
    console.log('Polling mode for deployment:', deploymentId);

    // Cleanup function
    return () => {
      setConnectionStatus('disconnected');
    };
  }, [deploymentId]);

  return {
    socket: null,
    messages,
    connectionStatus
  };
};
