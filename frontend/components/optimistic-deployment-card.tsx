'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { useToast } from '@/hooks/use-toast'
import { 
  useCreateDeployment, 
  useDeleteDeployment, 
  useDeploymentStatus 
} from '@/hooks/use-api'
import { useOptimisticUpdates } from '@/lib/react-query-provider'
import { 
  Play, 
  Square, 
  Trash2, 
  RotateCcw, 
  CheckCircle, 
  AlertTriangle,
  Clock,
  Loader2
} from 'lucide-react'

interface OptimisticDeploymentCardProps {
  deployment: {
    id: string
    name: string
    status: 'pending' | 'deploying' | 'success' | 'failed' | 'cancelled'
    progress?: number
    environment: string
    repository: string
    branch: string
    createdAt: string
    updatedAt: string
  }
  onOptimisticUpdate?: (id: string, updates: any) => void
}

export function OptimisticDeploymentCard({ 
  deployment, 
  onOptimisticUpdate 
}: OptimisticDeploymentCardProps) {
  const { toast } = useToast()
  const [isLocallyUpdating, setIsLocallyUpdating] = useState(false)
  
  // React Query mutations
  const createDeployment = useCreateDeployment()
  const deleteDeployment = useDeleteDeployment()
  
  // Real-time status hook
  const { 
    status, 
    progress, 
    isDeploying, 
    isSuccess, 
    isFailed 
  } = useDeploymentStatus(deployment.id)
  
  // Optimistic updates
  const optimisticUpdates = useOptimisticUpdates()
  
  const handleStartDeployment = async () => {
    if (deployment.status !== 'pending') return
    
    // Optimistic update - immediately show as deploying
    setIsLocallyUpdating(true)
    optimisticUpdates.updateDeploymentStatus(deployment.id, 'deploying', 0)
    onOptimisticUpdate?.(deployment.id, { status: 'deploying', progress: 0 })
    
    try {
      // Simulate API call to start deployment
      await new Promise(resolve => setTimeout(resolve, 1000))
      
      // Start progress simulation
      simulateProgress()
      
      toast({
        title: "Deployment Started",
        description: `${deployment.name} is now deploying to ${deployment.environment}`,
      })
    } catch (error) {
      // Revert optimistic update on error
      optimisticUpdates.updateDeploymentStatus(deployment.id, 'pending', 0)
      onOptimisticUpdate?.(deployment.id, { status: 'pending', progress: 0 })
      
      toast({
        title: "Deployment Failed to Start",
        description: "Please try again later.",
        variant: "destructive",
      })
    } finally {
      setIsLocallyUpdating(false)
    }
  }
  
  const handleCancelDeployment = async () => {
    if (!isDeploying) return
    
    // Optimistic update
    setIsLocallyUpdating(true)
    optimisticUpdates.updateDeploymentStatus(deployment.id, 'cancelled', deployment.progress)
    onOptimisticUpdate?.(deployment.id, { status: 'cancelled' })
    
    try {
      await new Promise(resolve => setTimeout(resolve, 500))
      
      toast({
        title: "Deployment Cancelled",
        description: `${deployment.name} deployment has been cancelled`,
      })
    } catch (error) {
      // Revert on error
      optimisticUpdates.updateDeploymentStatus(deployment.id, 'deploying', deployment.progress)
      onOptimisticUpdate?.(deployment.id, { status: 'deploying' })
      
      toast({
        title: "Failed to Cancel",
        description: "Could not cancel the deployment.",
        variant: "destructive",
      })
    } finally {
      setIsLocallyUpdating(false)
    }
  }
  
  const handleRetryDeployment = async () => {
    if (deployment.status !== 'failed') return
    
    // Optimistic update - reset to deploying
    setIsLocallyUpdating(true)
    optimisticUpdates.updateDeploymentStatus(deployment.id, 'deploying', 0)
    onOptimisticUpdate?.(deployment.id, { status: 'deploying', progress: 0 })
    
    try {
      await new Promise(resolve => setTimeout(resolve, 1000))
      simulateProgress()
      
      toast({
        title: "Deployment Retried",
        description: `Retrying deployment for ${deployment.name}`,
      })
    } catch (error) {
      optimisticUpdates.updateDeploymentStatus(deployment.id, 'failed', 0)
      onOptimisticUpdate?.(deployment.id, { status: 'failed' })
      
      toast({
        title: "Retry Failed",
        description: "Could not retry the deployment.",
        variant: "destructive",
      })
    } finally {
      setIsLocallyUpdating(false)
    }
  }
  
  const handleDeleteDeployment = async () => {
    if (isDeploying) return
    
    // Optimistic removal
    optimisticUpdates.removeDeployment(deployment.id)
    
    try {
      await deleteDeployment.mutateAsync(deployment.id)
      
      toast({
        title: "Deployment Deleted",
        description: `${deployment.name} has been removed`,
      })
    } catch (error) {
      // Re-add on error (would need to fetch from server in real app)
      optimisticUpdates.addDeployment(deployment)
      
      toast({
        title: "Delete Failed",
        description: "Could not delete the deployment.",
        variant: "destructive",
      })
    }
  }
  
  // Simulate deployment progress for demo
  const simulateProgress = () => {
    let currentProgress = 0
    const interval = setInterval(() => {
      currentProgress += Math.random() * 15
      
      if (currentProgress >= 100) {
        currentProgress = 100
        // Random success/failure for demo
        const success = Math.random() > 0.3
        optimisticUpdates.updateDeploymentStatus(
          deployment.id, 
          success ? 'success' : 'failed', 
          100
        )
        onOptimisticUpdate?.(deployment.id, { 
          status: success ? 'success' : 'failed', 
          progress: 100 
        })
        clearInterval(interval)
      } else {
        optimisticUpdates.updateDeploymentStatus(deployment.id, 'deploying', currentProgress)
        onOptimisticUpdate?.(deployment.id, { progress: currentProgress })
      }
    }, 1000)
  }
  
  const getStatusIcon = () => {
    const currentStatus = status || deployment.status
    
    switch (currentStatus) {
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      case 'deploying':
        return <Loader2 className="h-4 w-4 text-blue-500 animate-spin" />
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <AlertTriangle className="h-4 w-4 text-red-500" />
      case 'cancelled':
        return <Square className="h-4 w-4 text-gray-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }
  
  const getStatusBadge = () => {
    const currentStatus = status || deployment.status
    
    const variants: Record<string, "secondary" | "default" | "destructive"> = {
      pending: 'secondary',
      deploying: 'default',
      success: 'default',
      failed: 'destructive',
      cancelled: 'secondary',
    }
    
    return (
      <Badge variant={variants[currentStatus] || 'secondary'} className="flex items-center space-x-1">
        {getStatusIcon()}
        <span className="capitalize">{currentStatus}</span>
      </Badge>
    )
  }
  
  const currentProgress = progress ?? deployment.progress ?? 0
  const currentStatus = status || deployment.status
  
  return (
    <Card className="relative overflow-hidden">
      {/* Loading overlay for local updates */}
      {isLocallyUpdating && (
        <div className="absolute inset-0 bg-background/50 backdrop-blur-sm z-10 flex items-center justify-center">
          <Loader2 className="h-6 w-6 animate-spin" />
        </div>
      )}
      
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">{deployment.name}</CardTitle>
          {getStatusBadge()}
        </div>
        <div className="flex items-center space-x-4 text-sm text-muted-foreground">
          <span>{deployment.repository}</span>
          <span>•</span>
          <span>{deployment.branch}</span>
          <span>•</span>
          <Badge variant="outline" className="text-xs">
            {deployment.environment}
          </Badge>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress bar for deploying status */}
        {currentStatus === 'deploying' && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span>Deployment Progress</span>
              <span>{Math.round(currentProgress)}%</span>
            </div>
            <Progress value={currentProgress} className="h-2" />
          </div>
        )}
        
        {/* Action buttons */}
        <div className="flex items-center space-x-2">
          {currentStatus === 'pending' && (
            <Button
              onClick={handleStartDeployment}
              disabled={isLocallyUpdating}
              size="sm"
              className="flex items-center space-x-1"
            >
              <Play className="h-3 w-3" />
              <span>Deploy</span>
            </Button>
          )}
          
          {currentStatus === 'deploying' && (
            <Button
              onClick={handleCancelDeployment}
              disabled={isLocallyUpdating}
              variant="outline"
              size="sm"
              className="flex items-center space-x-1"
            >
              <Square className="h-3 w-3" />
              <span>Cancel</span>
            </Button>
          )}
          
          {currentStatus === 'failed' && (
            <Button
              onClick={handleRetryDeployment}
              disabled={isLocallyUpdating}
              variant="outline"
              size="sm"
              className="flex items-center space-x-1"
            >
              <RotateCcw className="h-3 w-3" />
              <span>Retry</span>
            </Button>
          )}
          
          {!isDeploying && (
            <Button
              onClick={handleDeleteDeployment}
              disabled={deleteDeployment.isPending || isLocallyUpdating}
              variant="outline"
              size="sm"
              className="flex items-center space-x-1 text-red-600 hover:text-red-700"
            >
              <Trash2 className="h-3 w-3" />
              <span>Delete</span>
            </Button>
          )}
        </div>
        
        {/* Timestamps */}
        <div className="text-xs text-muted-foreground space-y-1">
          <div>Created: {new Date(deployment.createdAt).toLocaleString()}</div>
          <div>Updated: {new Date(deployment.updatedAt).toLocaleString()}</div>
        </div>
      </CardContent>
    </Card>
  )
}
