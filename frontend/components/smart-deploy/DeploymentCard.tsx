// Deployment Card - Individual deployment status card with actions
'use client';

import React, { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { 
  ExternalLink, 
  Play, 
  Pause, 
  MoreVertical, 
  Eye, 
  Trash2,
  Download,
  Settings,
  Clock,
  CheckCircle,
  XCircle,
  Activity,
  Zap,
  Terminal
} from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface DeploymentCardProps {
  deployment: {
    id: string;
    project_name: string;
    status: 'analyzing' | 'generating' | 'deploying' | 'completed' | 'failed';
    progress: number;
    cloud_provider: string;
    environment: string;
    created_at: string;
    estimated_completion?: string;
    deployment_url?: string;
  };
  onRefresh: () => void;
}

export function DeploymentCard({ deployment, onRefresh }: DeploymentCardProps) {
  const [isLoading, setIsLoading] = useState(false);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle className="h-4 w-4 text-green-500" />;
      case 'failed': return <XCircle className="h-4 w-4 text-red-500" />;
      case 'deploying': return <Activity className="h-4 w-4 text-blue-500 animate-pulse" />;
      case 'generating': return <Zap className="h-4 w-4 text-purple-500 animate-pulse" />;
      case 'analyzing': return <Terminal className="h-4 w-4 text-yellow-500 animate-pulse" />;
      default: return <Clock className="h-4 w-4 text-gray-500" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'bg-green-100 text-green-800 border-green-200';
      case 'failed': return 'bg-red-100 text-red-800 border-red-200';
      case 'deploying': return 'bg-blue-100 text-blue-800 border-blue-200';
      case 'generating': return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'analyzing': return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      default: return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getCloudProviderIcon = (provider: string) => {
    switch (provider) {
      case 'aws': return '🌩️';
      case 'gcp': return '☁️';
      case 'azure': return '🔷';
      default: return '☁️';
    }
  };

  const getEnvironmentColor = (env: string) => {
    switch (env) {
      case 'development': return 'bg-yellow-100 text-yellow-800';
      case 'staging': return 'bg-orange-100 text-orange-800';
      case 'production': return 'bg-green-100 text-green-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const handleViewLogs = async () => {
    try {
      const response = await fetch(`/api/v1/smart-deploy/deployment/${deployment.id}/logs`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });
      
      if (response.ok) {
        const logs = await response.json();
        console.log('Deployment logs:', logs);
        // In a real implementation, this would open a logs modal
      }
    } catch (error) {
      console.error('Failed to fetch logs:', error);
    }
  };

  const handleDelete = async () => {
    if (window.confirm('Are you sure you want to delete this deployment?')) {
      setIsLoading(true);
      try {
        const response = await fetch(`/api/v1/smart-deploy/deployment/${deployment.id}`, {
          method: 'DELETE',
          headers: {
            'Authorization': `Bearer ${localStorage.getItem('token')}`
          }
        });

        if (response.ok) {
          onRefresh();
        }
      } catch (error) {
        console.error('Failed to delete deployment:', error);
      } finally {
        setIsLoading(false);
      }
    }
  };

  const handleExecuteDeployment = async () => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/smart-deploy/deployment/${deployment.id}/deploy`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        onRefresh();
      }
    } catch (error) {
      console.error('Failed to execute deployment:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const canExecute = deployment.status === 'completed' && !deployment.deployment_url;
  const canViewSite = deployment.status === 'completed' && deployment.deployment_url;

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="flex items-center gap-2">
              {getStatusIcon(deployment.status)}
              <CardTitle className="text-lg">{deployment.project_name}</CardTitle>
            </div>
            <Badge className={getStatusColor(deployment.status)}>
              {deployment.status.replace('_', ' ')}
            </Badge>
          </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreVertical className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={handleViewLogs}>
                <Eye className="h-4 w-4 mr-2" />
                View Logs
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Download className="h-4 w-4 mr-2" />
                Download Config
              </DropdownMenuItem>
              <DropdownMenuItem>
                <Settings className="h-4 w-4 mr-2" />
                Settings
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-red-600" onClick={handleDelete}>
                <Trash2 className="h-4 w-4 mr-2" />
                Delete
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
        <CardDescription className="flex items-center gap-2">
          <span>{getCloudProviderIcon(deployment.cloud_provider)}</span>
          <span className="capitalize">{deployment.cloud_provider}</span>
          <span>•</span>
          <Badge variant="outline" className={getEnvironmentColor(deployment.environment)}>
            {deployment.environment}
          </Badge>
          <span>•</span>
          <span>{formatDate(deployment.created_at)}</span>
        </CardDescription>
      </CardHeader>
      
      <CardContent className="space-y-4">
        {/* Progress Bar (only show for active deployments) */}
        {['analyzing', 'generating', 'deploying'].includes(deployment.status) && (
          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="font-medium">Progress</span>
              <span>{Math.round(deployment.progress)}%</span>
            </div>
            <Progress value={deployment.progress} className="h-2" />
            {deployment.estimated_completion && (
              <p className="text-xs text-gray-600">
                Estimated completion: {deployment.estimated_completion}
              </p>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex items-center gap-2">
          {canViewSite && (
            <Button
              size="sm"
              className="flex items-center gap-2"
              onClick={() => window.open(deployment.deployment_url, '_blank')}
            >
              <ExternalLink className="h-4 w-4" />
              View Site
            </Button>
          )}
          
          {canExecute && (
            <Button
              size="sm"
              variant="outline"
              className="flex items-center gap-2"
              onClick={handleExecuteDeployment}
              disabled={isLoading}
            >
              <Play className="h-4 w-4" />
              Deploy
            </Button>
          )}

          {deployment.status === 'deploying' && (
            <Button
              size="sm"
              variant="outline"
              className="flex items-center gap-2"
              disabled
            >
              <Pause className="h-4 w-4" />
              Deploying...
            </Button>
          )}

          <Button
            size="sm"
            variant="ghost"
            className="flex items-center gap-2"
            onClick={handleViewLogs}
          >
            <Terminal className="h-4 w-4" />
            Logs
          </Button>
        </div>

        {/* Deployment URL */}
        {deployment.deployment_url && (
          <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-green-800">Deployment URL</p>
                <p className="text-sm text-green-600 break-all">{deployment.deployment_url}</p>
              </div>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => {
                  navigator.clipboard.writeText(deployment.deployment_url || '');
                }}
              >
                Copy
              </Button>
            </div>
          </div>
        )}

        {/* Error message for failed deployments */}
        {deployment.status === 'failed' && (
          <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm font-medium text-red-800">Deployment Failed</p>
            <p className="text-sm text-red-600">
              Check the logs for more details about the failure.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
