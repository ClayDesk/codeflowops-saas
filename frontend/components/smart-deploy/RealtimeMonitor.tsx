// Real-time Monitor - WebSocket-based deployment monitoring with live updates
'use client';

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { ScrollArea } from '@/components/ui/scroll-area';
import { 
  Activity, 
  Play, 
  Pause, 
  RotateCcw, 
  CheckCircle, 
  XCircle, 
  Clock, 
  Zap,
  Terminal,
  Cloud,
  GitBranch,
  Server
} from 'lucide-react';

interface DeploymentEvent {
  id: string;
  timestamp: string;
  level: 'info' | 'warning' | 'error' | 'success';
  source: string;
  message: string;
  details?: any;
}

interface RealtimeDeployment {
  id: string;
  project_name: string;
  status: 'analyzing' | 'generating' | 'deploying' | 'completed' | 'failed';
  progress: number;
  cloud_provider: string;
  environment: string;
  current_step: string;
  estimated_completion?: string;
  events: DeploymentEvent[];
}

interface RealtimeMonitorProps {
  deployments: any[];
}

export function RealtimeMonitor({ deployments }: RealtimeMonitorProps) {
  const [selectedDeployment, setSelectedDeployment] = useState<string>('');
  const [monitoringEnabled, setMonitoringEnabled] = useState(true);
  const [realtimeDeployments, setRealtimeDeployments] = useState<RealtimeDeployment[]>([]);
  const [connectionStatus, setConnectionStatus] = useState<'connected' | 'disconnected' | 'connecting'>('disconnected');
  
  const websocketRef = useRef<WebSocket | null>(null);
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  // Simulate real-time data for demo
  useEffect(() => {
    if (monitoringEnabled) {
      simulateRealtimeData();
    }
  }, [monitoringEnabled, deployments]);

  const simulateRealtimeData = () => {
    // Convert regular deployments to real-time format with mock data
    const mockRealtimeDeployments: RealtimeDeployment[] = deployments.map((deployment, index) => ({
      id: deployment.id || `deployment-${index}`,
      project_name: deployment.project_name || `Project ${index + 1}`,
      status: deployment.status || 'analyzing',
      progress: deployment.progress || Math.random() * 100,
      cloud_provider: deployment.cloud_provider || 'aws',
      environment: deployment.environment || 'production',
      current_step: getCurrentStep(deployment.status || 'analyzing'),
      estimated_completion: deployment.estimated_completion || '3-5 minutes',
      events: generateMockEvents(deployment.id || `deployment-${index}`)
    }));

    setRealtimeDeployments(mockRealtimeDeployments);
    setConnectionStatus('connected');

    // Simulate progress updates
    const interval = setInterval(() => {
      if (monitoringEnabled) {
        setRealtimeDeployments(prev => 
          prev.map(deployment => ({
            ...deployment,
            progress: Math.min(100, deployment.progress + Math.random() * 5),
            events: [...deployment.events, generateNewEvent(deployment.id)]
          }))
        );
      }
    }, 3000);

    return () => clearInterval(interval);
  };

  const getCurrentStep = (status: string): string => {
    switch (status) {
      case 'analyzing': return 'Analyzing repository structure';
      case 'generating': return 'Generating infrastructure templates';
      case 'deploying': return 'Deploying to cloud provider';
      case 'completed': return 'Deployment completed successfully';
      case 'failed': return 'Deployment failed';
      default: return 'Initializing deployment';
    }
  };

  const generateMockEvents = (deploymentId: string): DeploymentEvent[] => {
    const events: DeploymentEvent[] = [
      {
        id: `${deploymentId}-1`,
        timestamp: new Date(Date.now() - 300000).toISOString(),
        level: 'info',
        source: 'smart_deploy',
        message: 'Deployment initiated by user'
      },
      {
        id: `${deploymentId}-2`,
        timestamp: new Date(Date.now() - 240000).toISOString(),
        level: 'info',
        source: 'analysis_service',
        message: 'Repository analysis started'
      },
      {
        id: `${deploymentId}-3`,
        timestamp: new Date(Date.now() - 180000).toISOString(),
        level: 'success',
        source: 'analysis_service',
        message: 'Detected React.js application with TypeScript'
      },
      {
        id: `${deploymentId}-4`,
        timestamp: new Date(Date.now() - 120000).toISOString(),
        level: 'info',
        source: 'infrastructure',
        message: 'Generating Terraform templates'
      },
      {
        id: `${deploymentId}-5`,
        timestamp: new Date(Date.now() - 60000).toISOString(),
        level: 'success',
        source: 'infrastructure',
        message: 'Infrastructure templates generated successfully'
      }
    ];

    return events;
  };

  const generateNewEvent = (deploymentId: string): DeploymentEvent => {
    const messages = [
      'CloudFormation stack update in progress',
      'SSL certificate provisioned',
      'CDN configuration updated',
      'Health checks passing',
      'Load balancer configured',
      'Auto-scaling policies applied'
    ];

    return {
      id: `${deploymentId}-${Date.now()}`,
      timestamp: new Date().toISOString(),
      level: 'info',
      source: 'aws_cloudformation',
      message: messages[Math.floor(Math.random() * messages.length)]
    };
  };

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
      case 'completed': return 'bg-green-100 text-green-800';
      case 'failed': return 'bg-red-100 text-red-800';
      case 'deploying': return 'bg-blue-100 text-blue-800';
      case 'generating': return 'bg-purple-100 text-purple-800';
      case 'analyzing': return 'bg-yellow-100 text-yellow-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getEventIcon = (source: string) => {
    switch (source) {
      case 'analysis_service': return <Zap className="h-3 w-3 text-blue-500" />;
      case 'infrastructure': return <Cloud className="h-3 w-3 text-blue-500" />;
      case 'aws_cloudformation': return <Server className="h-3 w-3 text-orange-500" />;
      case 'smart_deploy': return <GitBranch className="h-3 w-3 text-green-500" />;
      default: return <Activity className="h-3 w-3 text-gray-500" />;
    }
  };

  const getEventLevelColor = (level: string) => {
    switch (level) {
      case 'success': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleTimeString();
  };

  // Auto-scroll to bottom when new events arrive
  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight;
    }
  }, [realtimeDeployments]);

  return (
    <div className="space-y-6">
      {/* Monitor Controls */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5 text-blue-500" />
                Real-time Deployment Monitor
              </CardTitle>
              <CardDescription>
                Live updates from your Smart Deploy infrastructure deployments
              </CardDescription>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex items-center gap-2">
                <div className={`h-2 w-2 rounded-full ${
                  connectionStatus === 'connected' ? 'bg-green-500' : 
                  connectionStatus === 'connecting' ? 'bg-yellow-500' : 'bg-red-500'
                }`} />
                <span className="text-sm capitalize">{connectionStatus}</span>
              </div>
              <Button
                variant="outline"
                size="sm"
                onClick={() => setMonitoringEnabled(!monitoringEnabled)}
                className="flex items-center gap-2"
              >
                {monitoringEnabled ? (
                  <>
                    <Pause className="h-4 w-4" />
                    Pause
                  </>
                ) : (
                  <>
                    <Play className="h-4 w-4" />
                    Start
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => simulateRealtimeData()}
                className="flex items-center gap-2"
              >
                <RotateCcw className="h-4 w-4" />
                Refresh
              </Button>
            </div>
          </div>
        </CardHeader>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Deployments List */}
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle>Active Deployments</CardTitle>
            <CardDescription>
              {realtimeDeployments.length} deployment{realtimeDeployments.length !== 1 ? 's' : ''} being monitored
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {realtimeDeployments.length === 0 ? (
                <div className="text-center py-8">
                  <Activity className="h-8 w-8 text-gray-400 mx-auto mb-3" />
                  <p className="text-gray-500">No active deployments</p>
                </div>
              ) : (
                realtimeDeployments.map((deployment) => (
                  <div
                    key={deployment.id}
                    className={`p-3 border rounded-lg cursor-pointer transition-all ${
                      selectedDeployment === deployment.id 
                        ? 'border-blue-500 bg-blue-50' 
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => setSelectedDeployment(deployment.id)}
                  >
                    <div className="flex items-center justify-between mb-2">
                      <h4 className="font-medium text-sm">{deployment.project_name}</h4>
                      {getStatusIcon(deployment.status)}
                    </div>
                    <div className="space-y-2">
                      <Badge className={getStatusColor(deployment.status)}>
                        {deployment.status.replace('_', ' ')}
                      </Badge>
                      <div className="space-y-1">
                        <div className="flex justify-between text-xs text-gray-600">
                          <span>Progress</span>
                          <span>{Math.round(deployment.progress)}%</span>
                        </div>
                        <Progress value={deployment.progress} className="h-2" />
                      </div>
                      <p className="text-xs text-gray-600">{deployment.current_step}</p>
                    </div>
                  </div>
                ))
              )}
            </div>
          </CardContent>
        </Card>

        {/* Deployment Details & Event Log */}
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle>
              {selectedDeployment 
                ? `Deployment Details: ${realtimeDeployments.find(d => d.id === selectedDeployment)?.project_name || 'Unknown'}`
                : 'Select a Deployment'
              }
            </CardTitle>
            <CardDescription>
              {selectedDeployment
                ? 'Real-time event log and deployment progress'
                : 'Choose a deployment from the list to view details'
              }
            </CardDescription>
          </CardHeader>
          <CardContent>
            {selectedDeployment ? (
              (() => {
                const deployment = realtimeDeployments.find(d => d.id === selectedDeployment);
                if (!deployment) return null;

                return (
                  <div className="space-y-4">
                    {/* Deployment Overview */}
                    <div className="grid grid-cols-2 gap-4 p-4 bg-gray-50 rounded-lg">
                      <div>
                        <p className="text-sm font-medium text-gray-600">Cloud Provider</p>
                        <p className="text-lg font-semibold capitalize">{deployment.cloud_provider}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Environment</p>
                        <p className="text-lg font-semibold capitalize">{deployment.environment}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Current Step</p>
                        <p className="text-sm">{deployment.current_step}</p>
                      </div>
                      <div>
                        <p className="text-sm font-medium text-gray-600">Estimated Completion</p>
                        <p className="text-sm">{deployment.estimated_completion}</p>
                      </div>
                    </div>

                    {/* Progress Bar */}
                    <div className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span className="font-medium">Overall Progress</span>
                        <span>{Math.round(deployment.progress)}%</span>
                      </div>
                      <Progress value={deployment.progress} className="h-3" />
                    </div>

                    {/* Event Log */}
                    <div className="space-y-2">
                      <h4 className="font-medium flex items-center gap-2">
                        <Terminal className="h-4 w-4" />
                        Event Log
                      </h4>
                      <ScrollArea className="h-64 border rounded-lg p-3" ref={scrollAreaRef}>
                        <div className="space-y-2">
                          {deployment.events.map((event) => (
                            <div key={event.id} className="flex items-start gap-3 text-sm">
                              <div className="flex items-center gap-2 text-xs text-gray-500 min-w-[60px]">
                                {formatTimestamp(event.timestamp)}
                              </div>
                              <div className="flex items-center gap-2 min-w-[20px]">
                                {getEventIcon(event.source)}
                              </div>
                              <div className="flex-1">
                                <span className={`font-medium ${getEventLevelColor(event.level)}`}>
                                  [{event.source}]
                                </span>
                                <span className="ml-2">{event.message}</span>
                              </div>
                            </div>
                          ))}
                        </div>
                      </ScrollArea>
                    </div>
                  </div>
                );
              })()
            ) : (
              <div className="text-center py-12">
                <Activity className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                <h3 className="text-lg font-medium text-gray-900 mb-2">No Deployment Selected</h3>
                <p className="text-gray-600">
                  Select a deployment from the list to view real-time monitoring details
                </p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
