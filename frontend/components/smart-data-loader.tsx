'use client'

import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { 
  RefreshCw, 
  Wifi, 
  WifiOff, 
  CheckCircle, 
  AlertCircle,
  Clock,
  TrendingUp,
  TrendingDown,
  Minus
} from 'lucide-react'

interface SmartDataLoaderProps<T> {
  queryKey: string[]
  queryFn: () => Promise<T>
  children: (data: T, isRefreshing: boolean) => React.ReactNode
  fallback?: React.ReactNode
  enableBackground?: boolean
  refreshInterval?: number
  title?: string
  className?: string
}

export function SmartDataLoader<T>({
  queryKey,
  queryFn,
  children,
  fallback,
  enableBackground = true,
  refreshInterval = 30000,
  title,
  className
}: SmartDataLoaderProps<T>) {
  const [lastSuccessTime, setLastSuccessTime] = useState<Date | null>(null)
  const [refreshCount, setRefreshCount] = useState(0)
  const [connectionStatus, setConnectionStatus] = useState<'online' | 'offline'>('online')
  
  const {
    data,
    isLoading,
    isError,
    isFetching,
    isRefetching,
    error,
    refetch,
    dataUpdatedAt,
    errorUpdatedAt
  } = useQuery({
    queryKey,
    queryFn,
    refetchInterval: enableBackground ? refreshInterval : false,
    refetchOnWindowFocus: true,
    refetchOnReconnect: 'always',
    staleTime: 30000, // Consider data stale after 30 seconds
    gcTime: 300000, // Keep in cache for 5 minutes
    retry: (failureCount, error: any) => {
      if (error?.status === 404 || error?.status === 401) {
        return false
      }
      return failureCount < 3
    },
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
  })
  
  // Track connection status
  useEffect(() => {
    const handleOnline = () => setConnectionStatus('online')
    const handleOffline = () => setConnectionStatus('offline')
    
    window.addEventListener('online', handleOnline)
    window.addEventListener('offline', handleOffline)
    
    setConnectionStatus(navigator.onLine ? 'online' : 'offline')
    
    return () => {
      window.removeEventListener('online', handleOnline)
      window.removeEventListener('offline', handleOffline)
    }
  }, [])
  
  // Update success time and refresh count
  useEffect(() => {
    if (data && !isError) {
      setLastSuccessTime(new Date(dataUpdatedAt))
      if (refreshCount === 0 || !isLoading) {
        setRefreshCount(prev => prev + 1)
      }
    }
  }, [data, isError, dataUpdatedAt, isLoading, refreshCount])
  
  const handleManualRefresh = () => {
    refetch()
  }
  
  const formatTimeAgo = (date: Date) => {
    const now = new Date()
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000)
    
    if (diffInSeconds < 60) return 'Just now'
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)}m ago`
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)}h ago`
    return date.toLocaleDateString()
  }
  
  const getStatusIndicator = () => {
    if (connectionStatus === 'offline') {
      return (
        <Badge variant="destructive" className="flex items-center space-x-1">
          <WifiOff className="h-3 w-3" />
          <span>Offline</span>
        </Badge>
      )
    }
    
    if (isError) {
      return (
        <Badge variant="destructive" className="flex items-center space-x-1">
          <AlertCircle className="h-3 w-3" />
          <span>Error</span>
        </Badge>
      )
    }
    
    if (isRefetching) {
      return (
        <Badge variant="secondary" className="flex items-center space-x-1">
          <RefreshCw className="h-3 w-3 animate-spin" />
          <span>Updating</span>
        </Badge>
      )
    }
    
    if (data) {
      return (
        <Badge variant="default" className="flex items-center space-x-1">
          <Wifi className="h-3 w-3" />
          <span>Live</span>
        </Badge>
      )
    }
    
    return (
      <Badge variant="secondary" className="flex items-center space-x-1">
        <Clock className="h-3 w-3" />
        <span>Loading</span>
      </Badge>
    )
  }
  
  const getDataFreshness = () => {
    if (!lastSuccessTime) return null
    
    const now = new Date()
    const ageInSeconds = Math.floor((now.getTime() - lastSuccessTime.getTime()) / 1000)
    
    if (ageInSeconds < 60) {
      return (
        <div className="flex items-center space-x-1 text-green-600">
          <TrendingUp className="h-3 w-3" />
          <span className="text-xs">Fresh</span>
        </div>
      )
    } else if (ageInSeconds < 300) { // 5 minutes
      return (
        <div className="flex items-center space-x-1 text-yellow-600">
          <Minus className="h-3 w-3" />
          <span className="text-xs">Recent</span>
        </div>
      )
    } else {
      return (
        <div className="flex items-center space-x-1 text-red-600">
          <TrendingDown className="h-3 w-3" />
          <span className="text-xs">Stale</span>
        </div>
      )
    }
  }
  
  // Handle initial loading
  if (isLoading && !data) {
    return (
      <div className={className}>
        {title && (
          <Card>
            <CardHeader className="pb-2">
              <div className="flex items-center justify-between">
                <CardTitle className="text-lg">{title}</CardTitle>
                <Badge variant="secondary" className="flex items-center space-x-1">
                  <RefreshCw className="h-3 w-3 animate-spin" />
                  <span>Loading</span>
                </Badge>
              </div>
            </CardHeader>
          </Card>
        )}
        {fallback || (
          <Card>
            <CardContent className="p-6">
              <div className="space-y-4">
                <Skeleton className="h-4 w-full" />
                <Skeleton className="h-4 w-3/4" />
                <Skeleton className="h-4 w-1/2" />
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    )
  }
  
  // Handle error state
  if (isError && !data) {
    return (
      <div className={className}>
        <Card>
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{title || 'Data Loading Error'}</CardTitle>
              {getStatusIndicator()}
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-center py-8">
              <AlertCircle className="h-12 w-12 mx-auto mb-4 text-red-500" />
              <h3 className="text-lg font-semibold mb-2">Failed to Load Data</h3>
              <p className="text-muted-foreground mb-4">
                {error instanceof Error ? error.message : 'An unexpected error occurred'}
              </p>
              <Button onClick={handleManualRefresh} className="flex items-center space-x-2">
                <RefreshCw className="h-4 w-4" />
                <span>Try Again</span>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }
  
  // Render with data
  return (
    <div className={className}>
      {title && (
        <Card className="mb-4">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg">{title}</CardTitle>
              <div className="flex items-center space-x-2">
                {getStatusIndicator()}
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleManualRefresh}
                  disabled={isFetching}
                  className="flex items-center space-x-1"
                >
                  <RefreshCw className={`h-3 w-3 ${isFetching ? 'animate-spin' : ''}`} />
                  <span>Refresh</span>
                </Button>
              </div>
            </div>
            
            {/* Data status information */}
            <div className="flex items-center justify-between text-xs text-muted-foreground">
              <div className="flex items-center space-x-4">
                {lastSuccessTime && (
                  <span>Updated {formatTimeAgo(lastSuccessTime)}</span>
                )}
                <span>Refreshed {refreshCount} times</span>
              </div>
              {getDataFreshness()}
            </div>
          </CardHeader>
        </Card>
      )}
      
      {/* Background refresh indicator */}
      {isRefetching && !isLoading && (
        <div className="fixed top-4 right-4 z-50">
          <Badge className="flex items-center space-x-2 animate-pulse">
            <RefreshCw className="h-3 w-3 animate-spin" />
            <span>Updating data...</span>
          </Badge>
        </div>
      )}
      
      {children(data!, isRefetching)}
    </div>
  )
}

// Specialized version for deployment data
export function SmartDeploymentLoader({ children, className }: {
  children: (deployments: any[], isRefreshing: boolean) => React.ReactNode
  className?: string
}) {
  return (
    <SmartDataLoader
      queryKey={['deployments']}
      queryFn={async () => {
        // Using the actual backend endpoint
        const response = await fetch('http://localhost:8000/api/v1/smart-deploy/deployments')
        if (!response.ok) throw new Error('Failed to fetch deployments')
        return response.json()
      }}
      title="Deployments"
      className={className}
      refreshInterval={5000} // 5 second refresh for deployments
    >
      {(data, isRefreshing) => children(data?.data || [], isRefreshing)}
    </SmartDataLoader>
  )
}

// Specialized version for analytics data
export function SmartAnalyticsLoader({ children, className }: {
  children: (analytics: any, isRefreshing: boolean) => React.ReactNode
  className?: string
}) {
  return (
    <SmartDataLoader
      queryKey={['analytics']}
      queryFn={async () => {
        // Using the actual backend endpoint
        const response = await fetch('http://localhost:8000/api/v1/smart-deploy/stats')
        if (!response.ok) throw new Error('Failed to fetch analytics')
        return response.json()
      }}
      title="Analytics"
      className={className}
      refreshInterval={30000} // 30 second refresh for analytics
    >
      {children}
    </SmartDataLoader>
  )
}
