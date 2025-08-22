'use client'

import { useEffect, useState } from 'react'
import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { useDeployments, useAnalytics, useResourceUsage } from '@/hooks/use-api'
import { useOptimisticUpdates, useRealTimeSync } from '@/lib/react-query-provider'
import { 
  Activity, 
  AlertTriangle, 
  CheckCircle, 
  Clock, 
  Play, 
  Pause,
  RefreshCw,
  Server,
  Cpu,
  HardDrive,
  Wifi,
  WifiOff
} from 'lucide-react'

interface RealTimeStatusProps {
  className?: string
}

export function RealTimeStatus({ className }: RealTimeStatusProps) {
  const [isPolling, setIsPolling] = useState(true)
  const [lastUpdate, setLastUpdate] = useState(new Date())
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('connected')
  
  // React Query hooks with real-time polling
  const { 
    data: deployments, 
    isLoading: deploymentsLoading, 
    error: deploymentsError,
    refetch: refetchDeployments 
  } = useDeployments({ status: 'all' })
  
  const { 
    data: analytics, 
    isLoading: analyticsLoading,
    refetch: refetchAnalytics 
  } = useAnalytics('1d')
  
  const { 
    data: resourceUsage, 
    isLoading: resourceLoading,
    refetch: refetchResources 
  } = useResourceUsage()
  
  // Real-time sync utilities
  const { startPolling, stopPolling, syncOnVisibilityChange, syncOnFocus } = useRealTimeSync()
  const optimisticUpdates = useOptimisticUpdates()
  
  // Setup real-time polling and sync
  useEffect(() => {
    let deploymentInterval: NodeJS.Timeout
    let analyticsInterval: NodeJS.Timeout
    let resourceInterval: NodeJS.Timeout
    
    if (isPolling) {
      // Different polling intervals for different data types
      deploymentInterval = startPolling(['deployments'], 3000) // 3 seconds for deployments
      analyticsInterval = startPolling(['analytics'], 30000) // 30 seconds for analytics
      resourceInterval = startPolling(['resource-usage'], 5000) // 5 seconds for resources
      setConnectionStatus('connected')
    }
    
    return () => {
      if (deploymentInterval) stopPolling(deploymentInterval)
      if (analyticsInterval) stopPolling(analyticsInterval)
      if (resourceInterval) stopPolling(resourceInterval)
    }
  }, [isPolling, startPolling, stopPolling])
  
  // Setup visibility and focus sync
  useEffect(() => {
    const cleanupVisibility = syncOnVisibilityChange()
    const cleanupFocus = syncOnFocus()
    
    return () => {
      cleanupVisibility()
      cleanupFocus()
    }
  }, [syncOnVisibilityChange, syncOnFocus])
  
  // Update last update time when data changes
  useEffect(() => {
    if (deployments || analytics || resourceUsage) {
      setLastUpdate(new Date())
    }
  }, [deployments, analytics, resourceUsage])
  
  // Handle connection errors
  useEffect(() => {
    if (deploymentsError || analyticsLoading) {
      setConnectionStatus('disconnected')
    } else {
      setConnectionStatus('connected')
    }
  }, [deploymentsError, analyticsLoading])
  
  const handleRefresh = async () => {
    setConnectionStatus('connecting')
    try {
      await Promise.all([
        refetchDeployments(),
        refetchAnalytics(),
        refetchResources()
      ])
      setConnectionStatus('connected')
      setLastUpdate(new Date())
    } catch (error) {
      setConnectionStatus('disconnected')
    }
  }
  
  const togglePolling = () => {
    setIsPolling(!isPolling)
  }
  
  // Calculate active deployments
  const activeDeployments = deployments?.data?.filter(
    (d: any) => d.status === 'deploying' || d.status === 'pending'
  ) || []
  
  const successfulDeployments = deployments?.data?.filter(
    (d: any) => d.status === 'success'
  )?.length || 0
  
  const failedDeployments = deployments?.data?.filter(
    (d: any) => d.status === 'failed'
  )?.length || 0
  
  return (
    <div className={`space-y-4 ${className}`}>
      {/* Status Header */}
      <Card>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Real-time Status</CardTitle>
            <div className="flex items-center space-x-2">
              <Badge
                variant={connectionStatus === 'connected' ? 'default' : 'destructive'}
                className="flex items-center space-x-1"
              >
                {connectionStatus === 'connected' ? (
                  <Wifi className="h-3 w-3" />
                ) : (
                  <WifiOff className="h-3 w-3" />
                )}
                <span className="capitalize">{connectionStatus}</span>
              </Badge>
              <Button
                variant="outline"
                size="sm"
                onClick={togglePolling}
                className="flex items-center space-x-1"
              >
                {isPolling ? (
                  <Pause className="h-3 w-3" />
                ) : (
                  <Play className="h-3 w-3" />
                )}
                <span>{isPolling ? 'Pause' : 'Resume'}</span>
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={handleRefresh}
                disabled={connectionStatus === 'connecting'}
              >
                <RefreshCw 
                  className={`h-3 w-3 ${connectionStatus === 'connecting' ? 'animate-spin' : ''}`} 
                />
              </Button>
            </div>
          </div>
          <p className="text-sm text-muted-foreground">
            Last updated: {lastUpdate.toLocaleTimeString()}
          </p>
        </CardHeader>
      </Card>
      
      {/* Active Deployments */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Active Deployments</span>
            {activeDeployments.length > 0 && (
              <Badge variant="secondary">{activeDeployments.length}</Badge>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {deploymentsLoading ? (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <div key={i} className="flex items-center space-x-3">
                  <Skeleton className="h-4 w-4 rounded-full" />
                  <Skeleton className="h-4 flex-1" />
                  <Skeleton className="h-4 w-16" />
                </div>
              ))}
            </div>
          ) : activeDeployments.length === 0 ? (
            <div className="text-center py-4 text-muted-foreground">
              <CheckCircle className="h-8 w-8 mx-auto mb-2 text-green-500" />
              <p>No active deployments</p>
            </div>
          ) : (
            <div className="space-y-3">
              {activeDeployments.map((deployment: any) => (
                <div key={deployment.id} className="space-y-2">
                  <div className="flex items-center justify-between">
                    <div className="flex items-center space-x-2">
                      <div className={`h-2 w-2 rounded-full ${
                        deployment.status === 'deploying' ? 'bg-blue-500 animate-pulse' : 'bg-yellow-500'
                      }`} />
                      <span className="font-medium">{deployment.name}</span>
                      <Badge variant="outline" className="text-xs">
                        {deployment.environment}
                      </Badge>
                    </div>
                    <span className="text-sm text-muted-foreground">
                      {deployment.progress || 0}%
                    </span>
                  </div>
                  <Progress value={deployment.progress || 0} className="h-2" />
                  <p className="text-xs text-muted-foreground">
                    {deployment.currentStep || 'Initializing...'}
                  </p>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
      
      {/* Deployment Stats */}
      <div className="grid grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <CheckCircle className="h-5 w-5 text-green-500" />
              <div>
                <p className="text-2xl font-bold">
                  {deploymentsLoading ? (
                    <Skeleton className="h-8 w-8" />
                  ) : (
                    successfulDeployments
                  )}
                </p>
                <p className="text-xs text-muted-foreground">Successful</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <AlertTriangle className="h-5 w-5 text-red-500" />
              <div>
                <p className="text-2xl font-bold">
                  {deploymentsLoading ? (
                    <Skeleton className="h-8 w-8" />
                  ) : (
                    failedDeployments
                  )}
                </p>
                <p className="text-xs text-muted-foreground">Failed</p>
              </div>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center space-x-2">
              <Clock className="h-5 w-5 text-blue-500" />
              <div>
                <p className="text-2xl font-bold">
                  {analyticsLoading ? (
                    <Skeleton className="h-8 w-8" />
                  ) : (
                    Math.round(analytics?.averageDeployTime || 0)
                  )}
                </p>
                <p className="text-xs text-muted-foreground">Avg Time (min)</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
      
      {/* Resource Usage */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Server className="h-5 w-5" />
            <span>Resource Usage</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          {resourceLoading ? (
            <div className="space-y-4">
              {[1, 2, 3].map((i) => (
                <div key={i} className="space-y-2">
                  <Skeleton className="h-4 w-20" />
                  <Skeleton className="h-2 w-full" />
                </div>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Cpu className="h-4 w-4 text-blue-500" />
                    <span className="text-sm">CPU Usage</span>
                  </div>
                  <span className="text-sm font-medium">
                    {resourceUsage?.cpu || 0}%
                  </span>
                </div>
                <Progress value={resourceUsage?.cpu || 0} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <HardDrive className="h-4 w-4 text-green-500" />
                    <span className="text-sm">Memory Usage</span>
                  </div>
                  <span className="text-sm font-medium">
                    {resourceUsage?.memory || 0}%
                  </span>
                </div>
                <Progress value={resourceUsage?.memory || 0} className="h-2" />
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <HardDrive className="h-4 w-4 text-purple-500" />
                    <span className="text-sm">Storage Usage</span>
                  </div>
                  <span className="text-sm font-medium">
                    {resourceUsage?.storage || 0}%
                  </span>
                </div>
                <Progress value={resourceUsage?.storage || 0} className="h-2" />
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
