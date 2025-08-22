'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { API_CONFIG, buildApiUrl } from '@/lib/api-config'

// Simple API fetch helper
const fetchApi = async (url: string, options?: RequestInit) => {
  const response = await fetch(url, {
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
    ...options,
  })

  if (!response.ok) {
    throw new Error(`API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

// Repository Analysis Hook
export const useAnalyzeRepository = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (repositoryUrl: string) => {
      return fetchApi(buildApiUrl(API_CONFIG.ENDPOINTS.ANALYZE_REPO), {
        method: 'POST',
        body: JSON.stringify({ repository_url: repositoryUrl }),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['repository-analysis'] })
    },
  })
}

// Credentials Validation Hook
export const useValidateCredentials = () => {
  return useMutation({
    mutationFn: async (credentials: {
      aws_access_key: string
      aws_secret_key: string
      aws_region: string
    }) => {
      return fetchApi(buildApiUrl(API_CONFIG.ENDPOINTS.VALIDATE_CREDENTIALS), {
        method: 'POST',
        body: JSON.stringify(credentials),
      })
    },
  })
}

// Deployment Hook
export const useCreateDeployment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (deploymentData: {
      repository_url: string
      credential_id: string
      analysis: any
      deployment_config: any
    }) => {
      return fetchApi(buildApiUrl(API_CONFIG.ENDPOINTS.DEPLOY), {
        method: 'POST',
        body: JSON.stringify(deploymentData),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })
}

// Delete Deployment Hook (needed by optimistic-deployment-card.tsx)
export const useDeleteDeployment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (deploymentId: string) => {
      // This would need to be implemented in the backend
      return fetchApi(buildApiUrl(`/api/deployment/${deploymentId}`), {
        method: 'DELETE',
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })
}

// Deployment Status Hook (with custom interface for component compatibility)
export const useDeploymentStatus = (deploymentId: string, enabled = true) => {
  const { data, isLoading, error } = useQuery({
    queryKey: ['deployment-status', deploymentId],
    queryFn: () => fetchApi(buildApiUrl(API_CONFIG.ENDPOINTS.STATUS(deploymentId))),
    enabled: enabled && !!deploymentId,
    refetchInterval: 5000, // Poll every 5 seconds
  })

  return {
    status: data?.status,
    progress: data?.progress || 0,
    logs: data?.logs,
    isLoading,
    error,
    isDeploying: data?.status === 'deploying',
    isSuccess: data?.status === 'success' || data?.status === 'completed',
    isFailed: data?.status === 'failed',
  }
}

// Deployment URL Hook
export const useDeploymentUrl = (deploymentId: string, enabled = true) => {
  return useQuery({
    queryKey: ['deployment-url', deploymentId],
    queryFn: () => fetchApi(buildApiUrl(API_CONFIG.ENDPOINTS.URL(deploymentId))),
    enabled: enabled && !!deploymentId,
  })
}

// Health Check Hook
export const useHealthCheck = () => {
  return useQuery({
    queryKey: ['health-check'],
    queryFn: () => fetchApi(buildApiUrl(API_CONFIG.ENDPOINTS.HEALTH)),
    staleTime: 30000, // 30 seconds
  })
}

// Deployments List Hook (needed by real-time-status.tsx)
export const useDeployments = (filters?: any) => {
  return useQuery({
    queryKey: ['deployments', filters],
    queryFn: async () => {
      // Mock data since this endpoint doesn't exist in our simple backend
      return {
        data: [],
        total: 0,
        has_more: false
      }
    },
    staleTime: 30000,
  })
}

// Analytics Hook (needed by real-time-status.tsx)
export const useAnalytics = (timeRange: string = '24h') => {
  return useQuery({
    queryKey: ['analytics', timeRange],
    queryFn: async () => {
      // Mock analytics data with correct property names
      return {
        total_deployments: 0,
        successful_deployments: 0,
        failed_deployments: 0,
        averageDeployTime: 0  // Match the expected property name
      }
    },
    staleTime: 300000, // 5 minutes
  })
}

// Resource Usage Hook (needed by real-time-status.tsx)
export const useResourceUsage = () => {
  return useQuery({
    queryKey: ['resource-usage'],
    queryFn: async () => {
      // Mock resource usage data
      return {
        cpu: Math.floor(Math.random() * 100),
        memory: Math.floor(Math.random() * 100),
        storage: Math.floor(Math.random() * 100),
      }
    },
    staleTime: 15000, // 15 seconds
    refetchInterval: 15000,
  })
}

// Export types for the hooks
export type AnalysisResult = {
  deployment_id: string
  repository_url: string
  detected_framework: string
  project_type: string
  build_tool: string
  dependencies: string[]
  recommended_stack: any
  deployment_time: string
  status: string
}

export type DeploymentStatus = {
  deployment_id: string
  status: 'pending' | 'building' | 'deploying' | 'completed' | 'failed'
  progress: number
  message: string
  logs?: string[]
}

export type DeploymentUrl = {
  deployment_id: string
  website_url: string
  s3_bucket?: string
  cloudfront_url?: string
}