'use client'

import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { ReactNode, useState } from 'react'

// Create a QueryClient with optimal configuration
function makeQueryClient() {
  return new QueryClient({
    defaultOptions: {
      queries: {
        // With SSR, we usually want to set some default staleTime
        // above 0 to avoid refetching immediately on the client
        staleTime: 60 * 1000, // 1 minute
        retry: (failureCount, error: any) => {
          // Don't retry for 404s or auth errors
          if (error?.status === 404 || error?.status === 401) {
            return false
          }
          return failureCount < 3
        },
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
        refetchOnWindowFocus: true,
        refetchOnReconnect: true,
        // Background refetch when data is stale
        refetchOnMount: true,
      },
      mutations: {
        retry: 1,
        retryDelay: 1000,
      },
    },
  })
}

let browserQueryClient: QueryClient | undefined = undefined

function getQueryClient() {
  if (typeof window === 'undefined') {
    // Server: always make a new query client
    return makeQueryClient()
  } else {
    // Browser: make a new query client if we don't already have one
    // This is very important, so we don't re-make a new client if React
    // suspends during the initial render. This may not be needed if we
    // have a suspense boundary BELOW the creation of the query client
    if (!browserQueryClient) browserQueryClient = makeQueryClient()
    return browserQueryClient
  }
}

interface ReactQueryProviderProps {
  children: ReactNode
}

export default function ReactQueryProvider({ children }: ReactQueryProviderProps) {
  // NOTE: Avoid useState when initializing the query client if you don't
  //       have a suspense boundary between this and the code that may
  //       suspend because React will throw away the client on the initial
  //       render if it suspends and there is no boundary
  const queryClient = getQueryClient()

  return (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  )
}

// Hook for manual cache invalidation
export function useInvalidateQueries() {
  const queryClient = getQueryClient()
  
  return {
    invalidateAll: () => queryClient.invalidateQueries(),
    invalidateDeployments: () => queryClient.invalidateQueries({ queryKey: ['deployments'] }),
    invalidateAnalytics: () => queryClient.invalidateQueries({ queryKey: ['analytics'] }),
    invalidateTemplates: () => queryClient.invalidateQueries({ queryKey: ['templates'] }),
    invalidateUser: () => queryClient.invalidateQueries({ queryKey: ['user'] }),
    prefetchDeployment: (id: string) => 
      queryClient.prefetchQuery({
        queryKey: ['deployment', id],
        queryFn: async () => {
          // Using the actual backend endpoint
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api'}/v1/smart-deploy/status/${id}`)
          if (!response.ok) throw new Error('Failed to fetch deployment')
          return response.json()
        },
      }),
  }
}

// Optimistic update utilities
export function useOptimisticUpdates() {
  const queryClient = getQueryClient()
  
  return {
    updateDeploymentStatus: (deploymentId: string, status: string, progress?: number) => {
      // Update individual deployment
      queryClient.setQueryData(['deployment', deploymentId], (oldData: any) => ({
        ...oldData,
        status,
        progress: progress !== undefined ? progress : oldData?.progress,
        updatedAt: new Date().toISOString(),
      }))
      
      // Update deployments list
      queryClient.setQueryData(['deployments'], (oldData: any) => ({
        ...oldData,
        data: oldData?.data?.map((deployment: any) =>
          deployment.id === deploymentId 
            ? { ...deployment, status, progress: progress !== undefined ? progress : deployment.progress }
            : deployment
        ) || [],
      }))
    },
    
    updateAnalyticsMetric: (metric: string, value: number) => {
      queryClient.setQueryData(['analytics'], (oldData: any) => ({
        ...oldData,
        [metric]: value,
        lastUpdated: new Date().toISOString(),
      }))
    },
    
    addDeployment: (newDeployment: any) => {
      queryClient.setQueryData(['deployments'], (oldData: any) => ({
        ...oldData,
        data: [newDeployment, ...(oldData?.data || [])],
        total: (oldData?.total || 0) + 1,
      }))
    },
    
    removeDeployment: (deploymentId: string) => {
      queryClient.setQueryData(['deployments'], (oldData: any) => ({
        ...oldData,
        data: oldData?.data?.filter((deployment: any) => deployment.id !== deploymentId) || [],
        total: Math.max((oldData?.total || 1) - 1, 0),
      }))
    },
  }
}

// Real-time data sync utilities
export function useRealTimeSync() {
  const queryClient = getQueryClient()
  
  return {
    startPolling: (queryKey: string[], interval: number = 5000) => {
      queryClient.invalidateQueries({ queryKey })
      return setInterval(() => {
        queryClient.invalidateQueries({ queryKey })
      }, interval)
    },
    
    stopPolling: (intervalId: NodeJS.Timeout) => {
      clearInterval(intervalId)
    },
    
    syncOnVisibilityChange: () => {
      const handleVisibilityChange = () => {
        if (!document.hidden) {
          // User returned to tab, sync critical data
          queryClient.invalidateQueries({ queryKey: ['deployments'] })
          queryClient.invalidateQueries({ queryKey: ['analytics'] })
        }
      }
      
      document.addEventListener('visibilitychange', handleVisibilityChange)
      return () => document.removeEventListener('visibilitychange', handleVisibilityChange)
    },
    
    syncOnFocus: () => {
      const handleFocus = () => {
        queryClient.invalidateQueries({ queryKey: ['deployments'] })
      }
      
      window.addEventListener('focus', handleFocus)
      return () => window.removeEventListener('focus', handleFocus)
    },
  }
}
