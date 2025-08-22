'use client'

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { buildApiUrl, SmartApiConfig, STACK_TYPES, type StackType } from '@/lib/api-config-modular'

// Create a singleton instance of the smart API config
const smartApiConfig = new SmartApiConfig()

// Stack-specific deployment URL builder
const buildStackDeployUrl = (stackType: StackType): string => {
  return buildApiUrl(`/api/deploy/${stackType}`)
}

// Enhanced API fetch helper with fallback support
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

// Repository Analysis Hook (Enhanced for Stack Detection)
export const useAnalyzeRepository = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (repositoryUrl: string) => {
      const url = smartApiConfig.getApiUrl('/api/analyze-repo')
      const response = await fetchApi(url, {
        method: 'POST',
        body: JSON.stringify({ 
          repo_url: repositoryUrl,
          analysis_type: 'full'
        }),
      })
      
      // Add stack type detection info
      return {
        ...response,
        stack_detected: response.detected_stack || 'generic',
        stack_recommended: response.recommended_stack || response.detected_stack || 'generic',
        deployment_url: response.detected_stack ? buildStackDeployUrl(response.detected_stack) : null
      }
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
      const url = smartApiConfig.getApiUrl('/api/validate-credentials')
      return fetchApi(url, {
        method: 'POST',
        body: JSON.stringify(credentials),
      })
    },
  })
}

// Stack-Specific Deployment Hook (NEW - uses modular routing)
export const useStackDeployment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (deploymentData: {
      session_id: string
      stack_type: StackType
      project_name: string
      repo_url: string
      branch?: string
      config?: Record<string, any>
      credentials: {
        aws_access_key: string
        aws_secret_key: string
        aws_region: string
      }
    }) => {
      // Use stack-specific deployment endpoint
      const url = buildStackDeployUrl(deploymentData.stack_type)
      
      return fetchApi(url, {
        method: 'POST',
        body: JSON.stringify({
          session_id: deploymentData.session_id,
          project_name: deploymentData.project_name,
          repo_url: deploymentData.repo_url,
          branch: deploymentData.branch || 'main',
          aws_region: deploymentData.credentials.aws_region,
          ...deploymentData.config
        }),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })
}

// Legacy Deployment Hook (fallback for unsupported stacks)
export const useLegacyDeployment = () => {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async (deploymentData: {
      repository_url: string
      credential_id: string
      analysis: any
      deployment_config: any
    }) => {
      const url = buildApiUrl('/api/deploy') // Use integrated API
      return fetchApi(url, {
        method: 'POST',
        body: JSON.stringify(deploymentData),
      })
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployments'] })
    },
  })
}

// Get Available Stacks Hook (Modular API only)
export const useAvailableStacks = () => {
  return useQuery({
    queryKey: ['available-stacks'],
    queryFn: async () => {
      const url = buildApiUrl('/api/stacks/available')
      return fetchApi(url)
    },
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: 1
  })
}

// Deployment Status Hook (works with both APIs)
export const useDeploymentStatus = (deploymentId: string, enabled = true) => {
  return useQuery({
    queryKey: ['deployment-status', deploymentId],
    queryFn: async () => {
      const url = smartApiConfig.getApiUrl(`/api/deployment/${deploymentId}/status`)
      return fetchApi(url)
    },
    enabled: !!deploymentId && enabled,
    refetchInterval: (query) => {
      // Stop polling if deployment is complete
      const data = query.state.data
      if (data?.status === 'completed' || data?.status === 'failed') {
        return false
      }
      return 3000 // Poll every 3 seconds
    }
  })
}

// Deployment Result Hook
export const useDeploymentResult = (deploymentId: string, enabled = true) => {
  return useQuery({
    queryKey: ['deployment-result', deploymentId],
    queryFn: async () => {
      const url = smartApiConfig.getApiUrl(`/api/deployment/${deploymentId}/result`)
      return fetchApi(url)
    },
    enabled: !!deploymentId && enabled,
  })
}

// API Health Check Hook
export const useApiHealth = () => {
  return useQuery({
    queryKey: ['api-health'],
    queryFn: async () => {
      try {
        // Try modular system health endpoint
        const healthUrl = buildApiUrl('/api/system/health')
        const healthResponse = await fetchApi(healthUrl)
        
        return {
          modular: healthResponse,
          legacy: null,
          using: healthResponse.modular_system ? 'modular' : 'legacy'
        }
      } catch {
        // Fall back to basic health check
        try {
          const basicUrl = buildApiUrl('/api/health')
          const basicResponse = await fetchApi(basicUrl)
          
          return {
            modular: null,
            legacy: basicResponse,
            using: 'legacy'
          }
        } catch {
          return {
            modular: null,
            legacy: null,
            using: 'none'
          }
        }
      }
    },
    staleTime: 30 * 1000, // 30 seconds
    retry: 2
  })
}

// Smart Deployment Hook - automatically chooses best API based on stack
export const useSmartDeployment = () => {
  const stackDeployment = useStackDeployment()
  const legacyDeployment = useLegacyDeployment()
  
  return useMutation({
    mutationFn: async (data: {
      analysis: any
      credentials: {
        aws_access_key: string
        aws_secret_key: string
        aws_region: string
      }
      project_name: string
      repo_url: string
    }) => {
      const stackType = data.analysis.detected_stack || data.analysis.stack_detected || 'generic'
      
      // Check if we have a specific router for this stack
      if (smartApiConfig.isModularAvailable() && stackType !== 'generic') {
        // Use stack-specific deployment
        return stackDeployment.mutateAsync({
          session_id: `session-${Date.now()}`,
          stack_type: stackType as StackType,
          project_name: data.project_name,
          repo_url: data.repo_url,
          credentials: data.credentials,
          config: {
            // Pass analysis data as configuration
            detected_stack: stackType,
            analysis: data.analysis
          }
        })
      } else {
        // Fall back to legacy deployment
        return legacyDeployment.mutateAsync({
          repository_url: data.repo_url,
          credential_id: 'temp-cred-id',
          analysis: data.analysis,
          deployment_config: {
            aws_access_key_id: data.credentials.aws_access_key,
            aws_secret_access_key: data.credentials.aws_secret_key,
            aws_region: data.credentials.aws_region
          }
        })
      }
    }
  })
}

// Export stack types for use in components
export { STACK_TYPES }
export type { StackType }
