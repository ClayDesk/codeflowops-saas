/**
 * Enhanced Pipeline Integration Component
 * Additive enhancement - preserves all existing functionality
 * Integrates with comprehensive backend pipeline system
 */
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { 
  Activity, 
  GitBranch, 
  Cloud, 
  Zap, 
  CheckCircle, 
  AlertCircle,
  Clock,
  ArrowRight,
  Eye,
  Settings
} from 'lucide-react';

interface PipelineStatus {
  pipeline_id: string;
  stage: 'orchestration' | 'analysis' | 'deployment' | 'verification' | 'complete';
  status: 'pending' | 'running' | 'completed' | 'failed';
  progress: number;
  current_step: string;
  orchestrator_status?: any;
  blue_green_status?: any;
  enhanced_features?: any;
}

interface EnhancedPipelineIntegrationProps {
  deploymentId?: string;
  repositoryUrl?: string;
  onPipelineComplete?: (result: any) => void;
  // Preserve existing props compatibility
  existingProps?: any;
}

export const EnhancedPipelineIntegration: React.FC<EnhancedPipelineIntegrationProps> = ({
  deploymentId,
  repositoryUrl,
  onPipelineComplete,
  existingProps
}) => {
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [orchestrationLogs, setOrchestrationLogs] = useState<string[]>([]);
  const [blueGreenEnabled, setBlueGreenEnabled] = useState(false);
  const [multiTenantMode, setMultiTenantMode] = useState(false);
  
  // Integration with comprehensive backend pipeline
  useEffect(() => {
    if (deploymentId) {
      connectToComprehensivePipeline();
    }
  }, [deploymentId]);

  const connectToComprehensivePipeline = async () => {
    try {
      // Connect to orchestrator.py pipeline
      const response = await fetch(`/api/pipeline/status/${deploymentId}`);
      const status = await response.json();
      setPipelineStatus(status);

      // Subscribe to real-time updates
      subscribeToOrchestrationUpdates();
    } catch (error) {
      console.error('Pipeline connection error:', error);
    }
  };

  const subscribeToOrchestrationUpdates = () => {
    // WebSocket connection to comprehensive pipeline
    const ws = new WebSocket(`ws://localhost:8000/ws/pipeline/${deploymentId}`);
    
    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      setPipelineStatus(prev => ({ ...prev, ...update }));
      
      if (update.orchestration_logs) {
        setOrchestrationLogs(prev => [...prev, ...update.orchestration_logs]);
      }
    };
  };

  const enableBlueGreenDeployment = async () => {
    try {
      await fetch(`/api/pipeline/${deploymentId}/blue-green`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ enabled: true })
      });
      setBlueGreenEnabled(true);
    } catch (error) {
      console.error('Blue-green enablement error:', error);
    }
  };

  const PipelineVisualization = () => (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Activity className="h-5 w-5" />
          Comprehensive Pipeline Status
        </CardTitle>
        <CardDescription>
          Real-time orchestration and deployment pipeline monitoring
        </CardDescription>
      </CardHeader>
      <CardContent>
        {pipelineStatus && (
          <div className="space-y-6">
            {/* Pipeline Progress */}
            <div>
              <div className="flex justify-between mb-2">
                <span className="text-sm font-medium">{pipelineStatus.current_step}</span>
                <span className="text-sm text-muted-foreground">{pipelineStatus.progress}%</span>
              </div>
              <Progress value={pipelineStatus.progress} className="h-2" />
            </div>

            {/* Pipeline Stages */}
            <div className="grid grid-cols-5 gap-4">
              {['orchestration', 'analysis', 'deployment', 'verification', 'complete'].map((stage, index) => (
                <div key={stage} className="flex flex-col items-center space-y-2">
                  <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                    pipelineStatus.stage === stage ? 'bg-primary text-primary-foreground' :
                    index < ['orchestration', 'analysis', 'deployment', 'verification', 'complete'].indexOf(pipelineStatus.stage) ? 
                    'bg-green-500 text-white' : 'bg-muted text-muted-foreground'
                  }`}>
                    {pipelineStatus.stage === stage ? (
                      <Clock className="h-4 w-4" />
                    ) : index < ['orchestration', 'analysis', 'deployment', 'verification', 'complete'].indexOf(pipelineStatus.stage) ? (
                      <CheckCircle className="h-4 w-4" />
                    ) : (
                      <span className="text-xs">{index + 1}</span>
                    )}
                  </div>
                  <span className="text-xs font-medium capitalize">{stage}</span>
                </div>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );

  const OrchestrationControls = () => (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Pipeline Controls
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Blue-Green Deployment Toggle */}
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Blue-Green Deployment</p>
            <p className="text-sm text-muted-foreground">
              Enable zero-downtime deployments
            </p>
          </div>
          <Button
            variant={blueGreenEnabled ? "default" : "outline"}
            size="sm"
            onClick={enableBlueGreenDeployment}
            disabled={blueGreenEnabled}
          >
            {blueGreenEnabled ? "Enabled" : "Enable"}
          </Button>
        </div>

        {/* Multi-Tenant Mode */}
        <div className="flex items-center justify-between">
          <div>
            <p className="font-medium">Multi-Tenant Mode</p>
            <p className="text-sm text-muted-foreground">
              Deploy across multiple environments
            </p>
          </div>
          <Button
            variant={multiTenantMode ? "default" : "outline"}
            size="sm"
            onClick={() => setMultiTenantMode(!multiTenantMode)}
          >
            {multiTenantMode ? "Enabled" : "Enable"}
          </Button>
        </div>

        {/* Pipeline Insights */}
        <Alert>
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            Enhanced pipeline features integrate seamlessly with your existing deployment workflow.
          </AlertDescription>
        </Alert>
      </CardContent>
    </Card>
  );

  return (
    <div className="space-y-6">
      <Tabs defaultValue="pipeline" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="pipeline">Pipeline Status</TabsTrigger>
          <TabsTrigger value="controls">Controls</TabsTrigger>
          <TabsTrigger value="logs">Orchestration Logs</TabsTrigger>
        </TabsList>
        
        <TabsContent value="pipeline">
          <PipelineVisualization />
        </TabsContent>
        
        <TabsContent value="controls">
          <OrchestrationControls />
        </TabsContent>
        
        <TabsContent value="logs">
          <Card>
            <CardHeader>
              <CardTitle>Orchestration Logs</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="bg-muted p-4 rounded-lg max-h-96 overflow-y-auto">
                {orchestrationLogs.length > 0 ? (
                  <div className="space-y-1 font-mono text-sm">
                    {orchestrationLogs.map((log, index) => (
                      <div key={index} className="text-foreground">
                        {log}
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-muted-foreground">No orchestration logs available</p>
                )}
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default EnhancedPipelineIntegration;
