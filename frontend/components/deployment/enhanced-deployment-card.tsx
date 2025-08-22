'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu'
import {
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  AlertCircle,
  ExternalLink,
  MoreHorizontal,
  Play,
  Pause,
  RotateCcw,
  Trash2,
  Eye,
  Download,
  Settings
} from 'lucide-react'
import { cn } from '@/lib/utils'

interface Deployment {
  id: string
  name?: string
  project_name: string
  status: string
  environment: string
  cloud_provider: string
  created_at: string
  updated_at?: string
  url?: string
  monthly_cost?: number
  github_repo?: string
  domain_name?: string
  progress?: number
  framework?: string
  region?: string
}

interface DeploymentCardProps {
  deployment: Deployment
  onRefresh?: () => void
  onAction?: (action: string, deploymentId: string) => void
}

export function DeploymentCard({ deployment, onRefresh, onAction }: DeploymentCardProps) {
  const [isLoading, setIsLoading] = useState(false)

  const getStatusColor = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'completed':
      case 'running':
        return 'bg-green-100 text-green-800 border-green-200'
      case 'failed':
      case 'error':
        return 'bg-red-100 text-red-800 border-red-200'
      case 'pending':
      case 'building':
      case 'deploying':
      case 'analyzing':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200'
      case 'stopped':
        return 'bg-gray-100 text-gray-800 border-gray-200'
      default:
        return 'bg-blue-100 text-blue-800 border-blue-200'
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'success':
      case 'completed':
      case 'running':
        return <CheckCircle className="h-4 w-4" />
      case 'failed':
      case 'error':
        return <XCircle className="h-4 w-4" />
      case 'pending':
      case 'building':
      case 'deploying':
      case 'analyzing':
        return <Loader2 className="h-4 w-4 animate-spin" />
      case 'stopped':
        return <AlertCircle className="h-4 w-4" />
      default:
        return <Clock className="h-4 w-4" />
    }
  }

  const getCloudIcon = (provider: string) => {
    switch (provider?.toLowerCase()) {
      case 'aws':
        return '🌩️'
      case 'gcp':
        return '☁️'
      case 'azure':
        return '🔷'
      default:
        return '☁️'
    }
  }

  const handleAction = async (action: string) => {
    setIsLoading(true)
    try {
      if (onAction) {
        await onAction(action, deployment.id)
      }
      if (onRefresh) {
        onRefresh()
      }
    } catch (error) {
      console.error(`Failed to ${action} deployment:`, error)
    } finally {
      setIsLoading(false)
    }
  }

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    const now = new Date()
    const diffInMinutes = Math.floor((now.getTime() - date.getTime()) / (1000 * 60))
    
    if (diffInMinutes < 60) {
      return `${diffInMinutes} minutes ago`
    } else if (diffInMinutes < 1440) {
      return `${Math.floor(diffInMinutes / 60)} hours ago`
    } else {
      return date.toLocaleDateString()
    }
  }

  const getProgressValue = () => {
    if (deployment.progress !== undefined) {
      return deployment.progress
    }
    
    // Estimate progress based on status
    switch (deployment.status?.toLowerCase()) {
      case 'analyzing':
        return 25
      case 'building':
        return 50
      case 'deploying':
        return 75
      case 'completed':
      case 'success':
        return 100
      case 'failed':
      case 'error':
        return 0
      default:
        return 0
    }
  }

  return (
    <Card className="hover:shadow-md transition-all duration-200 group">
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <CardTitle className="text-lg">
                {deployment.name || deployment.project_name}
              </CardTitle>
              <span className="text-lg">{getCloudIcon(deployment.cloud_provider)}</span>
            </div>
            <CardDescription className="flex items-center gap-2">
              <span className="capitalize">{deployment.cloud_provider}</span>
              <span>•</span>
              <span className="capitalize">{deployment.environment}</span>
              {deployment.region && (
                <>
                  <span>•</span>
                  <span>{deployment.region}</span>
                </>
              )}
            </CardDescription>
          </div>
          
          <div className="flex items-center gap-2">
            <Badge className={cn("border", getStatusColor(deployment.status))}>
              {getStatusIcon(deployment.status)}
              <span className="ml-1 capitalize">{deployment.status}</span>
            </Badge>
            
            <DropdownMenu>
              <DropdownMenuTrigger asChild>
                <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                  <MoreHorizontal className="h-4 w-4" />
                </Button>
              </DropdownMenuTrigger>
              <DropdownMenuContent align="end">
                <DropdownMenuItem asChild>
                  <Link href={`/dashboard/deployments/${deployment.id}`}>
                    <Eye className="h-4 w-4 mr-2" />
                    View Details
                  </Link>
                </DropdownMenuItem>
                
                {deployment.url && (
                  <DropdownMenuItem asChild>
                    <a href={deployment.url} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Open Live Site
                    </a>
                  </DropdownMenuItem>
                )}
                
                <DropdownMenuSeparator />
                
                <DropdownMenuItem onClick={() => handleAction('restart')} disabled={isLoading}>
                  <RotateCcw className="h-4 w-4 mr-2" />
                  Restart
                </DropdownMenuItem>
                
                <DropdownMenuItem onClick={() => handleAction('stop')} disabled={isLoading}>
                  <Pause className="h-4 w-4 mr-2" />
                  Stop
                </DropdownMenuItem>
                
                <DropdownMenuItem onClick={() => handleAction('download')} disabled={isLoading}>
                  <Download className="h-4 w-4 mr-2" />
                  Download Logs
                </DropdownMenuItem>
                
                <DropdownMenuSeparator />
                
                <DropdownMenuItem onClick={() => handleAction('settings')} disabled={isLoading}>
                  <Settings className="h-4 w-4 mr-2" />
                  Settings
                </DropdownMenuItem>
                
                <DropdownMenuItem 
                  onClick={() => handleAction('delete')} 
                  disabled={isLoading}
                  className="text-red-600 focus:text-red-600"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Delete
                </DropdownMenuItem>
              </DropdownMenuContent>
            </DropdownMenu>
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress Bar for in-progress deployments */}
        {['analyzing', 'building', 'deploying'].includes(deployment.status?.toLowerCase()) && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-gray-600">Progress</span>
              <span className="font-medium">{getProgressValue()}%</span>
            </div>
            <Progress value={getProgressValue()} className="h-2" />
          </div>
        )}
        
        {/* Deployment Info Grid */}
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <p className="text-gray-600">Created</p>
            <p className="font-medium">{formatDate(deployment.created_at)}</p>
          </div>
          
          <div>
            <p className="text-gray-600">Cost/Month</p>
            <p className="font-medium text-green-600">
              ${deployment.monthly_cost?.toFixed(2) || '12.50'}
            </p>
          </div>
          
          {deployment.framework && (
            <div>
              <p className="text-gray-600">Framework</p>
              <p className="font-medium">{deployment.framework}</p>
            </div>
          )}
          
          {deployment.url && (
            <div>
              <p className="text-gray-600">Status</p>
              <a 
                href={deployment.url} 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-600 hover:text-blue-800 font-medium inline-flex items-center gap-1"
              >
                Live Site
                <ExternalLink className="h-3 w-3" />
              </a>
            </div>
          )}
        </div>
        
        {/* Additional Info */}
        {deployment.github_repo && (
          <div className="pt-2 border-t">
            <p className="text-xs text-gray-600 mb-1">Repository</p>
            <a 
              href={deployment.github_repo} 
              target="_blank" 
              rel="noopener noreferrer"
              className="text-xs text-blue-600 hover:text-blue-800 inline-flex items-center gap-1"
            >
              {deployment.github_repo.replace('https://github.com/', '')}
              <ExternalLink className="h-3 w-3" />
            </a>
          </div>
        )}
        
        {/* Quick Actions */}
        <div className="flex gap-2 pt-2">
          <Button 
            variant="outline" 
            size="sm" 
            asChild
            className="flex-1"
          >
            <Link href={`/dashboard/deployments/${deployment.id}`}>
              <Eye className="h-4 w-4 mr-1" />
              View
            </Link>
          </Button>
          
          {deployment.url && (
            <Button 
              variant="outline" 
              size="sm" 
              asChild
              className="flex-1"
            >
              <a href={deployment.url} target="_blank" rel="noopener noreferrer">
                <ExternalLink className="h-4 w-4 mr-1" />
                Open
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
