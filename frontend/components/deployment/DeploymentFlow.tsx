/**
 * Repository Deployment Flow Component
 * Handles the complete GitHub-to-AWS deployment workflow
 */

import React, { useState } from 'react';
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { API_CONFIG } from '@/lib/api-config';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Separator } from '@/components/ui/separator';
import {
  Github,
  Globe,
  Settings,
  Zap,
  CheckCircle,
  AlertTriangle,
  Clock,
  ArrowRight,
  ExternalLink,
  Eye,
  UploadCloud
} from 'lucide-react';
import { Skeleton } from '@/components/ui/skeleton';
import SimpleCredentialInput from '@/components/credential-management/SimpleCredentialInput';
import { AuthProtected } from '@/components/auth/AuthProtected';

// Visual step metadata (Preview included). Internal state still uses 3.5 for Preview for backward compatibility.
const stepsMeta = [
  { label: 'Repository', icon: <Github className="w-5 h-5" /> },
  { label: 'Analysis', icon: <Settings className="w-5 h-5" /> },
  { label: 'Credentials', icon: <Zap className="w-5 h-5" /> },
  { label: 'Preview', icon: <Eye className="w-5 h-5" /> },
  { label: 'Deploy', icon: <Clock className="w-5 h-5" /> },
  { label: 'Complete', icon: <CheckCircle className="w-5 h-5" /> }
];

interface RepoAnalysis {
  repository_name?: string;
  framework: string;
  detected_framework?: string;
  language: string;
  build_tool?: string;
  dependencies: string[];
  infrastructure: {
    compute: 'static' | 'react';
    storage: string[];
    networking: string[];
  };
  deployment_strategy: string;
  build_commands: string[];
  environment_variables: string[];
  // 🔥 Enhanced database and security information
  database_detected?: boolean;
  database_types?: string[];
  security_validations?: Array<{
    type: string;
    message: string;
    severity: 'info' | 'warning' | 'error';
  }>;
  baas_platforms?: string[];
  security_status?: 'secure' | 'warning' | 'error';
}

interface DeploymentStatus {
  step: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  message: string;
  progress: number;
  timestamp: string;
  logs?: string[];
}

interface DeploymentFlowProps {
  onComplete?: (deploymentInfo: any) => void;
  onCancel?: () => void;
}

const DeploymentFlow: React.FC<DeploymentFlowProps> = ({ onComplete, onCancel }) => {
  return (
    <AuthProtected>
      <DeploymentFlowContent onComplete={onComplete} onCancel={onCancel} />
    </AuthProtected>
  );
};

const DeploymentFlowContent: React.FC<DeploymentFlowProps> = ({ onComplete, onCancel }) => {
  // Lightweight presentational helpers (UI only)
  const AnalysisSection: React.FC<{title: string; defaultOpen?: boolean; children: React.ReactNode}> = ({ title, defaultOpen = false, children }) => (
    <details className="group rounded-md border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-3" open={defaultOpen}>
      <summary className="cursor-pointer select-none list-none font-medium text-sm flex items-center justify-between">
        <span>{title}</span>
        <span className="ml-2 text-xs text-gray-500 group-open:hidden">Expand</span>
        <span className="ml-2 text-xs text-gray-500 hidden group-open:inline">Collapse</span>
      </summary>
      <div className="mt-3 space-y-3 text-sm">{children}</div>
    </details>
  );

  const PreviewSection: React.FC<{title: string; defaultOpen?: boolean; children: React.ReactNode}> = ({ title, defaultOpen = false, children }) => (
    <details className="group rounded-md border border-gray-200 dark:border-gray-800 bg-white dark:bg-gray-900 px-4 py-3" open={defaultOpen}>
      <summary className="cursor-pointer select-none list-none font-semibold text-sm flex items-center justify-between">
        <span>{title}</span>
        <span className="ml-2 text-xs text-gray-500 group-open:hidden">Expand</span>
        <span className="ml-2 text-xs text-gray-500 hidden group-open:inline">Collapse</span>
      </summary>
      <div className="mt-3 space-y-4 text-sm">{children}</div>
    </details>
  );

  const Info: React.FC<{label: string; value: React.ReactNode}> = ({ label, value }) => (
    <div className="space-y-0.5">
      <p className="text-xs font-medium text-gray-600 dark:text-gray-400">{label}</p>
      <p className="text-xs font-mono break-all">{value}</p>
    </div>
  );

  const ResultHeader: React.FC<{variant: 'success' | 'error'; title: string; icon: React.ReactNode; subtitle: string}> = ({ variant, title, icon, subtitle }) => (
    <div className={`text-center pb-4 ${variant === 'success' ? 'text-gray-900' : ''}`}>
      <div className={`mx-auto flex h-16 w-16 items-center justify-center rounded-full mb-4 ${variant === 'success' ? 'bg-green-100' : 'bg-red-100'}`}>{icon}</div>
      <h2 className={`text-2xl font-bold mb-2 ${variant === 'success' ? 'text-green-700' : 'text-red-700'}`}>{title}</h2>
      <p className={`text-sm ${variant === 'success' ? 'text-gray-600' : 'text-red-600'}`}>{subtitle}</p>
    </div>
  );
  const [step, setStep] = useState(1);
  const stepHeadingRef = React.useRef<HTMLHeadingElement | null>(null);
  React.useEffect(() => {
    const t = setTimeout(() => stepHeadingRef.current?.focus(), 30);
    return () => clearTimeout(t);
  }, [step]);
  const [githubUrl, setGithubUrl] = useState('');
  const [analysis, setAnalysis] = useState<RepoAnalysis | null>(null);
  const [githubUrlError, setGithubUrlError] = useState<string | null>(null); // inline validation message
  const [credentialId, setCredentialId] = useState<string | null>(null);

  // Helper function to determine if this is a static site
  const isStaticSite = (analysisData: any) => {
    if (!analysisData) return false;
    
    // Check backend plugin detection first
    if (analysisData.project_type === 'static' || analysisData.detected_framework === 'static') {
      return true;
    }
    
    // Check plugin detection object
    if (analysisData.plugin_detection && analysisData.plugin_detection.recommended_stack === 'static') {
      return true;
    }
    
    // Fallback to checking framework names
    const framework = (analysisData.framework || analysisData.detected_framework || '').toLowerCase();
    const language = (analysisData.primary_language || analysisData.language || '').toLowerCase();
    
    // Check for static site indicators - case insensitive
    return framework.includes('static') || 
           framework === 'html' || 
           language === 'html' ||
           framework === 'static site' ||
           (language === 'html' && !framework.includes('react') && !framework.includes('next'));
  };

  const [awsCredentials, setAwsCredentials] = useState<{
    access_key_id: string;
    secret_access_key: string;
    region: string;
  } | null>(null);
  const [deploymentId, setDeploymentId] = useState<string | null>(null);
  const [deploymentStatus, setDeploymentStatus] = useState<DeploymentStatus[]>([]);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [isDeploying, setIsDeploying] = useState(false);
  const [showSimpleCredentialInput, setShowSimpleCredentialInput] = useState(false);
  const [deploymentUrl, setDeploymentUrl] = useState<string | null>(null);
  const [simulatedProgress, setSimulatedProgress] = useState(45); // Start at 45% for deployment phase

  // Steps: 1=URL, 2=Analysis, 3=Credentials, 3.5=Deployment Preview, 4=Deploy, 5=Complete

  // Cleanup function for when component unmounts or user cancels
  const handleCleanup = async () => {
    if (deploymentId) {
      try {
        await fetch(`${API_CONFIG.BASE_URL}/api/deployment/${deploymentId}/cancel`, {
          method: 'DELETE'
        });
      } catch (error) {
        console.error('Failed to cleanup deployment:', error);
      }
    }
  };

  // Cleanup on component unmount (browser close, navigation away)
  React.useEffect(() => {
    return () => {
      handleCleanup();
    };
  }, [deploymentId]);

  // Smart progress simulation for better UX
  React.useEffect(() => {
    if (step === 4 && isDeploying) {
      const progressInterval = setInterval(() => {
        setSimulatedProgress(prev => {
          const completedSteps = deploymentStatus.filter(s => s.status === 'completed').length;
          const runningSteps = deploymentStatus.filter(s => s.status === 'running').length;
          
          // Calculate target based on actual progress - more responsive scaling
          let targetProgress = 50;
          
          // If we have deployment URL, force 100% completion
          if (deploymentUrl && deploymentUrl.includes('cloudfront.net')) {
            targetProgress = 100;
          } else {
            // Progressive calculation based on completed steps
            targetProgress = 50 + ((completedSteps + runningSteps * 0.7) / 6) * 50;
          }
          
          // Special handling for specific steps
          const infraStep = deploymentStatus.find(s => s.step.includes('Infrastructure'));
          const buildStep = deploymentStatus.find(s => s.step.includes('Building'));
          const uploadStep = deploymentStatus.find(s => s.step.includes('S3'));
          const cloudfrontStep = deploymentStatus.find(s => s.step.includes('CloudFront'));
          
          // More granular progress updates
          if (infraStep?.status === 'running') targetProgress = Math.max(targetProgress, 55);
          if (infraStep?.status === 'completed') targetProgress = Math.max(targetProgress, 65);
          if (buildStep?.status === 'running') targetProgress = Math.max(targetProgress, 70);
          if (buildStep?.status === 'completed') targetProgress = Math.max(targetProgress, 80);
          if (uploadStep?.status === 'running') targetProgress = Math.max(targetProgress, 85);
          if (uploadStep?.status === 'completed') targetProgress = Math.max(targetProgress, 90);
          
          // CloudFront special handling - cap at 85% during global deployment
          const isCloudFrontDeploying = cloudfrontStep?.status === 'running' && 
            (cloudfrontStep?.message?.includes('deploying globally') || 
             cloudfrontStep?.message?.includes('15-20 minutes'));
          
          if (isCloudFrontDeploying) {
            targetProgress = Math.min(targetProgress, 85);
          }
          
          // Smooth incremental progress towards target
          if (prev < targetProgress) {
            return Math.min(prev + 1, targetProgress); // Faster increment - 1% every 500ms
          } else if (prev > targetProgress) {
            return targetProgress; // Jump down if actual progress is lower
          }
          
          // If no real progress updates, slowly increment to show activity
          if (completedSteps === 0 && runningSteps === 0 && prev < 55) {
            return prev + 0.2; // Slow increment to show we're working
          }
          
          return prev;
        });
      }, 500); // Update every 500ms for smooth animation

      return () => clearInterval(progressInterval);
    } else {
      // Reset simulated progress for other steps
      if (step === 1) setSimulatedProgress(0);
      if (step === 2) setSimulatedProgress(15);
      if (step === 3) setSimulatedProgress(30);
      if (step === 3.5) setSimulatedProgress(45);
      if (step === 5) setSimulatedProgress(100);
    }
  }, [step, isDeploying, deploymentStatus]);

  // Handle user cancellation
  const handleCancel = async () => {
    await handleCleanup();
    if (onCancel) {
      onCancel();
    }
  };

  const validateGitHubUrl = (url: string): boolean => {
    const githubRegex = /^https:\/\/github\.com\/[\w-]+\/[\w.-]+\/?$/;
    return githubRegex.test(url);
  };

  const analyzeRepository = async () => {
    console.log('🔍 analyzeRepository called');
    console.log('🔍 GitHub URL:', githubUrl);
    console.log('🔍 URL validation result:', validateGitHubUrl(githubUrl));
    
    if (!validateGitHubUrl(githubUrl)) {
      setGithubUrlError('Enter a valid public GitHub repository URL (e.g. https://github.com/org/repo)');
      return;
    } else if (githubUrlError) {
      setGithubUrlError(null);
    }

    console.log('🚀 Starting repository analysis...');
    setIsAnalyzing(true);
    let result: any = null;
    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.ANALYZE_REPO}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ repository_url: githubUrl })
      });

      result = await response.json();
      
      if (response.ok) {
        console.log('Backend response:', result);
        // Transform the backend response to match frontend expectations
        // The backend returns: { analysis: { repository_name, project_types, ... } }
        const analysisData = result.analysis || result;
        console.log('Analysis data:', analysisData);
        const primaryType = analysisData.project_types?.[0] || {};
        console.log('Primary type:', primaryType);
        console.log('Dependencies from backend:', analysisData.dependencies, 'Type:', typeof analysisData.dependencies);
        console.log('Full dependencies object:', JSON.stringify(analysisData.dependencies, null, 2));
        
        // Convert dependencies object to array of actual package names
        let dependenciesArray: string[] = [];
        if (analysisData.dependencies) {
          if (Array.isArray(analysisData.dependencies)) {
            dependenciesArray = analysisData.dependencies;
          } else if (typeof analysisData.dependencies === 'object') {
            // Extract actual package names from each package manager
            const deps = analysisData.dependencies;
            const allPackages: string[] = [];
            
            // Get npm packages
            if (deps.npm && typeof deps.npm === 'object') {
              allPackages.push(...Object.keys(deps.npm));
            }
            
            // Get pip packages
            if (deps.pip && typeof deps.pip === 'object') {
              allPackages.push(...Object.keys(deps.pip));
            }
            
            // Get composer packages
            if (deps.composer && typeof deps.composer === 'object') {
              allPackages.push(...Object.keys(deps.composer));
            }
            
            // Get go packages
            if (deps.go && typeof deps.go === 'object') {
              allPackages.push(...Object.keys(deps.go));
            }
            
            // Get cargo packages
            if (deps.cargo && typeof deps.cargo === 'object') {
              allPackages.push(...Object.keys(deps.cargo));
            }
            
            dependenciesArray = allPackages;
          }
        }
        console.log('Transformed dependencies array:', dependenciesArray);
        
        const transformedResult: RepoAnalysis = {
          repository_name: analysisData.repository_name || githubUrl.split('/').pop()?.replace('.git', '') || 'unknown-repo',
          framework: analysisData.detected_framework || analysisData.project_type || primaryType.type || 'Static Site',
          language: analysisData.primary_language || analysisData.language || Object.keys(analysisData.languages || {})[0] || 'HTML',
          build_tool: analysisData.build_tool || (isStaticSite(analysisData) ? 'None' : 'npm'),
          dependencies: dependenciesArray,
          // Use only available stacks: static or react
          infrastructure: analysisData.infrastructure || {
            compute: isStaticSite(analysisData) ? "static" : "react",
            storage: ["S3"],
            networking: ["CloudFront", "Route 53"]
          },
          deployment_strategy: analysisData.deployment_strategy || (isStaticSite(analysisData)
            ? "Static S3 + CloudFront deployment" 
            : "React Build + S3 + CloudFront deployment"),
          build_commands: analysisData.build_commands || (isStaticSite(analysisData)
            ? [] 
            : ["npm install", "npm run build"]),
          environment_variables: analysisData.environment_variables || [],
          // 🔥 Enhanced database and security information
          database_detected: analysisData.database_detected || false,
          database_types: analysisData.database_types || [],
          security_validations: analysisData.security_validations || [],
          baas_platforms: analysisData.baas_platforms || [],
          security_status: analysisData.security_status || 'secure'
        };
        
        setAnalysis(transformedResult);
        // Set the deployment ID from the backend response
        if (result.deployment_id) {
          setDeploymentId(result.deployment_id);
        }
        setStep(2);
      } else {
        throw new Error(result.detail || 'Failed to analyze repository');
      }
    } catch (error: any) {
      console.error('Analysis failed:', error);
      if (result) {
        console.error('Response was:', result);
      }
  // Present failure inline instead of disruptive alert
  setGithubUrlError(`Failed to analyze repository: ${error.message || error}`);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const startDeployment = async () => {
    if (!analysis || !credentialId || !awsCredentials || !deploymentId) {
      alert('Missing analysis, credentials, or deployment ID');
      return;
    }

    setIsDeploying(true);
    setStep(4);

    // Initialize all deployment steps as pending
    const initialSteps: DeploymentStatus[] = [
      {
        step: "Infrastructure Provisioning",
        status: 'running',
        message: "Creating AWS S3 bucket and IAM roles...",
        progress: 0,
        timestamp: new Date().toISOString()
      },
      {
        step: "Repository Building",
        status: 'pending',
        message: "Waiting for infrastructure setup...",
        progress: 0,
        timestamp: new Date().toISOString()
      },
      {
        step: "S3 Upload", 
        status: 'pending',
        message: "Waiting for build completion...",
        progress: 0,
        timestamp: new Date().toISOString()
      },
      {
        step: "CloudFront Configuration",
        status: 'pending',
        message: "Waiting for file upload...",
        progress: 0,
        timestamp: new Date().toISOString()
      },
      {
        step: "SSL & DNS Setup",
        status: 'pending',
        message: "Waiting for CDN configuration...",
        progress: 0,
        timestamp: new Date().toISOString()
      },
      {
        step: "Deployment Complete",
        status: 'pending',
        message: "Finalizing deployment...",
        progress: 0,
        timestamp: new Date().toISOString()
      }
    ];
    
    setDeploymentStatus(initialSteps);

    try {
      const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.DEPLOY}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          deployment_id: deploymentId,
          // Pass credentials directly - no session storage needed
          aws_access_key: awsCredentials.access_key_id,
          aws_secret_key: awsCredentials.secret_access_key,
          aws_region: awsCredentials.region
        })
      });

      const result = await response.json();
      
      if (response.ok) {
        // Use the existing deployment ID (should be the same)
        // Start polling for deployment status
        startStatusPolling(deploymentId);
      } else {
        throw new Error(result.detail || 'Failed to start deployment');
      }
    } catch (error) {
      console.error('Deployment failed:', error);
      alert('Failed to start deployment. Please try again.');
      setIsDeploying(false);
    }
  };

  const startStatusPolling = (deploymentId: string) => {
    const pollStatus = async () => {
      try {
        const response = await fetch(`${API_CONFIG.BASE_URL}${API_CONFIG.ENDPOINTS.STATUS(deploymentId)}`, {
          headers: {
            'Authorization': `Bearer demo-token`
          }
        });

        const status = await response.json();
        
        // Merge backend status with our initialized steps
        if (status.steps && status.steps.length > 0) {
          setDeploymentStatus(prevSteps => {
            const updatedSteps = [...prevSteps];
            
            status.steps.forEach((backendStep: any) => {
              const existingIndex = updatedSteps.findIndex(step => 
                step.step === backendStep.step ||
                step.step.includes(backendStep.step) ||
                backendStep.step.includes(step.step)
              );
              
              if (existingIndex >= 0) {
                // Update existing step
                updatedSteps[existingIndex] = {
                  ...updatedSteps[existingIndex],
                  status: backendStep.status,
                  message: backendStep.message,
                  timestamp: backendStep.timestamp,
                  logs: backendStep.logs
                };
              } else {
                // Add new step if not found
                updatedSteps.push(backendStep);
              }
            });
            
            return updatedSteps;
          });
        }

        // Check if deployment is complete
        const lastStep = status.steps?.[status.steps.length - 1];
        const cloudfrontStep = status.steps?.find((step: any) => 
          step.step === 'CloudFront Configuration' || 
          step.step.includes('CloudFront')
        );
        
        // Navigate to success page when:
        // 1. We have a CloudFront deployment URL (even if still propagating)
        const isFullyComplete = status.deployment_url && 
          status.deployment_url.includes('cloudfront.net');
        
        if (isFullyComplete) {
          // Mark all steps as completed before transitioning
          setDeploymentStatus(prevSteps => {
            return prevSteps.map(step => ({
              ...step,
              status: 'completed',
              message: step.step === 'Deployment Complete' 
                ? `🌐 Live at: ${status.deployment_url}`
                : `${step.step} completed successfully`,
              timestamp: new Date().toISOString()
            }));
          });
          
          setDeploymentUrl(status.deployment_url);
          setStep(5);
          setIsDeploying(false);
          if (onComplete) {
            // Enhanced deployment info for success page
            const deploymentInfo = {
              deployment_id: deploymentId,
              deployment_url: status.deployment_url,
              repository_name: analysis?.repository_name || 'Unknown Repository',
              repository_url: githubUrl,
              framework: analysis?.framework || 'static',
              language: analysis?.language || 'HTML',
              s3_bucket: status.infrastructure?.bucket_name || '',
              cloudfront_id: status.infrastructure?.cloudfront_id || '',
              cloudfront_domain: status.infrastructure?.cloudfront_domain || '',
              files_uploaded: status.infrastructure?.files_uploaded || 0,
              steps: status.steps,
              logs: status.logs || []
            };
            onComplete(deploymentInfo);
          }
        } else if (lastStep?.status === 'completed' && lastStep?.step === 'Deployment Complete') {
          // Deployment steps are complete but CloudFront is still deploying
          // Update the UI to show CloudFront is still in progress
          setDeploymentStatus(prevSteps => {
            const updatedSteps = [...prevSteps];
            const cfIndex = updatedSteps.findIndex(step => 
              step.step === 'CloudFront Configuration' || 
              step.step.includes('CloudFront')
            );
            
            if (cfIndex >= 0) {
              updatedSteps[cfIndex] = {
                ...updatedSteps[cfIndex],
                status: 'running',
                message: 'CloudFront distribution deploying globally (15-20 minutes)...',
                timestamp: new Date().toISOString()
              };
            }
            
            return updatedSteps;
          });
          
          // Continue polling for CloudFront readiness
          setTimeout(pollStatus, 10000); // Poll every 10 seconds for CloudFront status
        } else if (lastStep?.status === 'failed') {
          setIsDeploying(false);
          setStep(6); // Move to failure step
          
          // Log the failure details for debugging
          console.error('Deployment failed:', lastStep);
          console.error('All deployment steps:', status.steps);
          
          // Show detailed error information
          const errorMessage = lastStep?.message || 'Unknown deployment error';
          if (errorMessage.includes('Build failed') || errorMessage.includes('npm')) {
            // Build-specific error handling
            console.error('Build process failed - check build logs');
          }
        } else {
          // Continue polling
          setTimeout(pollStatus, 2000); // Poll every 2 seconds for more responsive UI
        }
      } catch (error) {
        console.error('Failed to fetch deployment status:', error);
        setTimeout(pollStatus, 5000); // Retry in 5 seconds on error
      }
    };

    pollStatus();
  };

  // Simple credential handler - no storage needed
  const handleCredentialsValidated = (credentials: {
    access_key_id: string;
    secret_access_key: string;
    region: string;
  }) => {
    setAwsCredentials(credentials);
    setCredentialId(`validated-${Date.now()}`);
    setShowSimpleCredentialInput(false);
    setStep(3.5); // Go to deployment preview
  };

  const getOverallProgress = (): number => {
    if (step === 1) return 0;
    if (step === 2) return 15;
    if (step === 3) return 30;
    if (step === 3.5) return 45;
    if (step === 4) {
      // Use simulated progress for smooth, real-time updates during deployment
      return simulatedProgress;
    }
    if (step === 5) return 100;
    return 0;
  };

  // Enhanced function to get deployment step details
  const getDeploymentSteps = () => {
    const allSteps = [
      {
        name: "Infrastructure Setup",
        description: "Creating S3 bucket with static website hosting",
        icon: <Settings className="w-4 h-4" />
      },
      {
        name: "File Upload",
        description: "Uploading website files to S3 storage",
        icon: <UploadCloud className="w-4 h-4" />
      },
      {
        name: "CloudFront Distribution",
        description: "Setting up global CDN for fast worldwide access",
        icon: <Globe className="w-4 h-4" />
      },
      {
        name: "Security Configuration",
        description: "Enabling HTTPS and configuring access policies",
        icon: <Zap className="w-4 h-4" />
      },
      {
        name: "Final Verification",
        description: "Testing deployment and ensuring everything works",
        icon: <CheckCircle className="w-4 h-4" />
      },
      {
        name: "Deployment Complete",
        description: "Your website is now live and accessible globally!",
        icon: <CheckCircle className="w-4 h-4" />
      }
    ];

    return allSteps.map(stepTemplate => {
      // Map actual deployment status steps to our UI steps
      let actualStep = null;
      
      // Infrastructure setup
      if (stepTemplate.name === "Infrastructure Setup") {
        actualStep = deploymentStatus.find(s => 
          s.step.includes('Infrastructure') || 
          s.step.includes('S3') || 
          s.step.includes('bucket')
        );
      }
      // File upload
      else if (stepTemplate.name === "File Upload") {
        actualStep = deploymentStatus.find(s => 
          s.step.includes('Upload') || 
          s.step.includes('sync') || 
          s.step.includes('files')
        );
      }
      // CloudFront
      else if (stepTemplate.name === "CloudFront Distribution") {
        actualStep = deploymentStatus.find(s => 
          s.step.includes('CloudFront') || 
          s.step.includes('CDN')
        );
      }
      // Security
      else if (stepTemplate.name === "Security Configuration") {
        actualStep = deploymentStatus.find(s => 
          s.step.includes('SSL') || 
          s.step.includes('HTTPS') || 
          s.step.includes('security') ||
          s.step.includes('policy')
        );
      }
      // Final verification
      else if (stepTemplate.name === "Final Verification") {
        actualStep = deploymentStatus.find(s => 
          s.step.includes('verification') || 
          s.step.includes('testing') ||
          s.step.includes('validate')
        );
      }
      // Deployment complete
      else if (stepTemplate.name === "Deployment Complete") {
        actualStep = deploymentStatus.find(s => 
          s.step.includes('Complete') || 
          s.step.includes('Finished')
        );
      }
      
      // Override status if we have a deployment URL (all should be completed)
      let finalStatus = actualStep?.status || 'pending';
      let finalMessage = actualStep?.message || stepTemplate.description;
      
      if (deploymentUrl && deploymentUrl.includes('cloudfront.net')) {
        // If deployment is complete, all steps should show as completed
        finalStatus = 'completed';
        if (stepTemplate.name === "Deployment Complete") {
          finalMessage = `🌐 Live at: ${deploymentUrl}`;
        } else {
          finalMessage = `${stepTemplate.name} completed successfully`;
        }
      }
      
      // If we have actual deployment steps, show them, otherwise show our template steps
      return {
        ...stepTemplate,
        status: finalStatus,
        message: finalMessage,
        timestamp: actualStep?.timestamp || (finalStatus === 'completed' ? new Date().toISOString() : undefined),
        logs: actualStep?.logs
      };
    });
  };

  // Map internal numeric step (with 3.5) to visual index (1-6)
  const visualStep = React.useMemo(() => {
    if (step === 3.5) return 4; // Preview
    if (step >= 5) return 6; // Complete (success) / treat failure as terminal visual step too
    return step; // 1,2,3,4 (deploy), or 6 failure handled above
  }, [step]);

  if (showSimpleCredentialInput) {
    return (
      <SimpleCredentialInput
        onCredentialsValidated={handleCredentialsValidated}
        onCancel={() => setShowSimpleCredentialInput(false)}
      />
    );
  }

  return (
    <div className="max-w-4xl mx-auto p-6" aria-live="polite" aria-atomic="false">
      {/* Modern horizontal stepper */}
      <div className="mb-10" aria-label="Deployment steps">
        <div className="flex items-center justify-between gap-2 bg-gradient-to-r from-blue-50/60 via-purple-50/60 to-blue-100/60 dark:from-blue-950/60 dark:via-purple-950/60 dark:to-blue-900/60 rounded-2xl px-4 py-4 shadow-sm overflow-x-auto" role="list">
          {stepsMeta.map((s, idx) => {
            const active = visualStep === idx + 1;
            const completed = visualStep > idx + 1;
            return (
              <div
                key={s.label}
                className="flex-1 min-w-[90px] flex flex-col items-center relative"
                role="listitem"
                aria-current={active ? 'step' : undefined}
                aria-label={`${s.label} ${active ? ' (current step)' : completed ? ' (completed)' : ''}`.trim()}
              >
                <div
                  className={`flex items-center justify-center w-10 h-10 rounded-full border-2 transition-all duration-200
                  ${active
                    ? 'bg-gradient-to-br from-blue-600 to-purple-600 border-blue-600 text-white shadow-lg scale-110'
                    : completed
                      ? 'bg-green-500 border-green-500 text-white'
                      : 'bg-white dark:bg-gray-950 border-gray-300 dark:border-gray-800 text-gray-400'}
                `}
                  aria-hidden="true"
                >
                  {s.icon}
                </div>
                <span className={`mt-2 text-xs font-semibold tracking-wide text-center px-1
                  ${active ? 'text-blue-700 dark:text-blue-300' : completed ? 'text-green-600' : 'text-gray-400 dark:text-gray-500'}`}>{s.label}</span>
                {idx < stepsMeta.length - 1 && (
                  <div className="absolute top-5 right-0 w-full h-1 flex items-center justify-center" aria-hidden="true">
                    <div className={`h-1 w-full rounded bg-gradient-to-r from-blue-200 to-purple-200 dark:from-blue-900 dark:to-purple-900 transition-all duration-200
                      ${completed ? 'bg-green-400' : ''}`}></div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      </div>

      {/* Progress Bar */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-2">
          <span className="text-sm font-medium">Overall Progress</span>
          <span className="text-sm text-gray-500">{Math.round(getOverallProgress())}%</span>
        </div>
        <Progress value={getOverallProgress()} className="h-2 bg-gradient-to-r from-blue-200 to-purple-200 dark:from-blue-900 dark:to-purple-900" />
      </div>

      {/* Step 1: Repository URL */}
  {step === 1 && (
        <Card>
          <CardHeader>
    <CardTitle ref={stepHeadingRef as any} tabIndex={-1} className="flex items-center gap-2 focus:outline-none">
              <Github className="w-5 h-5" />
              Repository URL
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <Label htmlFor="github_url">GitHub Repository URL</Label>
              <Input
                id="github_url"
                value={githubUrl}
                onChange={(e) => {
                  setGithubUrl(e.target.value.trim());
                  if (githubUrlError) setGithubUrlError(null);
                }}
                aria-invalid={!!githubUrlError}
                aria-describedby="github_url_help"
                placeholder="https://github.com/username/repository"
                className={`mt-1 ${githubUrlError ? 'border-red-500 focus-visible:ring-red-500' : ''}`}
              />
              <p id="github_url_help" className={`text-sm mt-1 ${githubUrlError ? 'text-red-600' : 'text-gray-500'}`}>
                {githubUrlError || 'Enter the public GitHub repository URL you want to deploy'}
              </p>
            </div>

            <Alert>
              <Github className="w-4 h-4" />
              <AlertDescription>
                Our system will analyze your repository to determine the best AWS infrastructure and deployment strategy.
              </AlertDescription>
            </Alert>

            <div className="flex justify-end gap-3">
              {onCancel && (
                <Button variant="outline" onClick={handleCancel}>
                  Cancel
                </Button>
              )}
              <Button 
                onClick={() => {
                  console.log('🔘 Analyze button clicked!');
                  console.log('🔘 githubUrl:', githubUrl);
                  console.log('🔘 isAnalyzing:', isAnalyzing);
                  console.log('🔘 validation:', validateGitHubUrl(githubUrl));
                  analyzeRepository();
                }}
                disabled={!githubUrl || isAnalyzing || !validateGitHubUrl(githubUrl)}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze Repository'}
              </Button>
            </div>
          </CardContent>
        </Card>
      )}
      {/* Step 2: Analysis Results */}
  {step === 2 && analysis && (
        <div className="space-y-6">
          <Card>
            <CardHeader>
      <CardTitle ref={stepHeadingRef as any} tabIndex={-1} className="flex items-center gap-2 focus:outline-none">
                <Settings className="w-5 h-5" />
                Repository Analysis
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <h3 className="font-semibold mb-2">Technology Stack</h3>
                  <div className="space-y-2">
                    <div className="flex items-center gap-2">
                      <Badge variant="secondary">{analysis.framework}</Badge>
                      <Badge variant="outline">{analysis.language}</Badge>
                    </div>
                    <p className="text-sm text-gray-600">
                      Detected framework and primary language
                    </p>
                  </div>
                </div>

                <div>
                  <h3 className="font-semibold mb-2">Infrastructure Recommendation</h3>
                  <div className="space-y-2">
                    <Badge 
                      variant={analysis.infrastructure.compute === 'static' ? 'outline' : 'default'}
                      className="capitalize"
                    >
                      {analysis.infrastructure.compute === 'static' ? 'Static Site' : 'React App'}
                    </Badge>
                    <p className="text-sm text-gray-600">
                      {analysis.infrastructure.compute === 'static' 
                        ? 'Static hosting with S3 + CloudFront'
                        : 'React app hosting with S3 + CloudFront + CodeBuild'
                      }
                    </p>
                  </div>
                </div>
              </div>

              <Separator />

              <div>
                <h3 className="font-semibold mb-2">Dependencies ({Array.isArray(analysis.dependencies) ? analysis.dependencies.length : 0})</h3>
                <div className="max-h-32 overflow-y-auto">
                  <div className="flex flex-wrap gap-1">
                    {Array.isArray(analysis.dependencies) && analysis.dependencies.length > 0 ? (
                      <>
                        {analysis.dependencies.slice(0, 10).map((dep, index) => (
                          <Badge key={index} variant="outline" className="text-xs">
                            {dep}
                          </Badge>
                        ))}
                        {analysis.dependencies.length > 10 && (
                          <Badge variant="outline" className="text-xs">
                            +{analysis.dependencies.length - 10} more
                          </Badge>
                        )}
                      </>
                    ) : (
                      <Badge variant="outline" className="text-xs text-gray-500">
                        No dependencies found
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          <div className="flex justify-between">
            <Button variant="outline" onClick={() => setStep(1)}>
              Back
            </Button>
            <Button onClick={() => setStep(3)}>
              Continue to Credentials
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: AWS Credentials */}
  {step === 3 && (
        <Card>
          <CardHeader>
    <CardTitle ref={stepHeadingRef as any} tabIndex={-1} className="flex items-center gap-2 focus:outline-none">
              <Zap className="w-5 h-5" />
              AWS Credentials
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert>
              <Zap className="w-4 h-4" />
              <AlertDescription>
                Connect an AWS account used only for deployment automation. We use your keys transiently and never store secrets in plain text.
              </AlertDescription>
            </Alert>

            <details className="rounded border border-gray-200 dark:border-gray-800 bg-gray-50 dark:bg-gray-900 px-4 py-3 text-sm">
              <summary className="cursor-pointer select-none font-medium text-xs tracking-wide text-gray-700 dark:text-gray-300">
                What happens with my credentials?
              </summary>
              <ul className="mt-3 space-y-1 text-xs list-disc ml-5 text-gray-600 dark:text-gray-400">
                <li>Used only for provisioning required AWS resources (S3, CloudFront, IAM)</li>
                <li>Never committed or logged in plain text</li>
                <li>Can be rotated or removed anytime from your AWS console</li>
              </ul>
            </details>

            {credentialId ? (
              <div className="bg-green-50 border border-green-200 p-4 rounded-lg">
                <div className="flex items-center gap-2 text-green-800">
                  <CheckCircle className="w-5 h-5" />
                  <span className="font-semibold">AWS Credentials Ready</span>
                </div>
                <p className="text-green-700 text-sm mt-1">
                  Your AWS credentials have been validated and are ready for deployment.
                </p>
              </div>
            ) : (
              <div className="text-center py-8">
                <p className="text-gray-600 mb-4">
                  Set up your AWS credentials to continue with the deployment
                </p>
                <Button onClick={() => setShowSimpleCredentialInput(true)}>
                  Set Up AWS Credentials
                </Button>
              </div>
            )}

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(2)}>
                Back
              </Button>
              <Button 
                onClick={() => setStep(3.5)}
                disabled={!credentialId}
              >
                Preview Deployment
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 3.5: Deployment Preview */}
  {step === 3.5 && (
        <Card>
          <CardHeader>
    <CardTitle ref={stepHeadingRef as any} tabIndex={-1} className="flex items-center gap-2 focus:outline-none">
              <Eye className="w-5 h-5" />
              Deployment Preview
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert>
              <Eye className="w-4 h-4" />
              <AlertDescription>
                Review all resources that will be created during deployment. This includes your repository analysis and AWS infrastructure.
              </AlertDescription>
            </Alert>

            {/* Repository Analysis Summary */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Repository Analysis</h3>
              <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm font-medium text-gray-600">Repository</label>
                    <p className="text-sm">{analysis?.repository_name || 'Unknown'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Framework</label>
                    <p className="text-sm">{analysis?.framework || 'Static Site'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Language</label>
                    <p className="text-sm">{analysis?.language || 'HTML/CSS/JS'}</p>
                  </div>
                  <div>
                    <label className="text-sm font-medium text-gray-600">Build Tool</label>
                    <p className="text-sm">{analysis?.build_tool || 'None'}</p>
                  </div>
                </div>
                {analysis?.dependencies && analysis.dependencies.length > 0 && (
                  <div>
                    <label className="text-sm font-medium text-gray-600">Dependencies</label>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {analysis.dependencies.map((dep, index) => (
                        <span key={index} className="px-2 py-1 bg-blue-100 text-blue-800 text-xs rounded">
                          {dep}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* 🔥 Database & Security Analysis */}
            {analysis?.database_detected && (
              <div className="space-y-4">
                <h3 className="text-lg font-semibold flex items-center gap-2">
                  🔒 Database & Security Analysis
                </h3>
                <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                  {/* Database Types */}
                  {analysis.database_types && analysis.database_types.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Detected Databases</label>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {analysis.database_types.map((dbType, index) => (
                          <Badge key={index} variant="outline" className="flex items-center gap-1">
                            {dbType === 'firestore' && '🔥'}
                            {dbType === 'supabase' && '🟦'}
                            {dbType === 'postgresql' && '🐘'}
                            {dbType === 'mysql' && '🐬'}
                            {dbType === 'mongodb' && '🍃'}
                            {dbType}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* BaaS Platforms */}
                  {analysis.baas_platforms && analysis.baas_platforms.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">BaaS Platforms</label>
                      <div className="flex flex-wrap gap-2 mt-1">
                        {analysis.baas_platforms.map((platform, index) => (
                          <Badge key={index} variant="secondary" className="flex items-center gap-1">
                            {platform === 'firebase' && '🔥 Firebase'}
                            {platform === 'supabase' && '🟦 Supabase'}
                            {!['firebase', 'supabase'].includes(platform) && platform}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Security Status */}
                  <div>
                    <label className="text-sm font-medium text-gray-600">Security Status</label>
                    <div className="mt-1">
                      {analysis.security_status === 'secure' && (
                        <Badge variant="default" className="bg-green-500 flex items-center gap-1 w-fit">
                          <CheckCircle className="w-3 h-3" />
                          Secure Configuration
                        </Badge>
                      )}
                      {analysis.security_status === 'warning' && (
                        <Badge variant="destructive" className="bg-yellow-500 flex items-center gap-1 w-fit">
                          <AlertTriangle className="w-3 h-3" />
                          Requires Review
                        </Badge>
                      )}
                      {analysis.security_status === 'error' && (
                        <Badge variant="destructive" className="flex items-center gap-1 w-fit">
                          <AlertTriangle className="w-3 h-3" />
                          Security Issues Detected
                        </Badge>
                      )}
                    </div>
                  </div>

                  {/* Security Validations */}
                  {analysis.security_validations && analysis.security_validations.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Security Validations</label>
                      <div className="space-y-2 mt-1">
                        {analysis.security_validations.map((validation, index) => (
                          <Alert key={index} className={`
                            ${validation.severity === 'error' ? 'border-red-200 bg-red-50' : ''}
                            ${validation.severity === 'warning' ? 'border-yellow-200 bg-yellow-50' : ''}
                            ${validation.severity === 'info' ? 'border-blue-200 bg-blue-50' : ''}
                          `}>
                            <AlertDescription className="text-sm">
                              <span className="flex items-center gap-2">
                                {validation.severity === 'error' && <AlertTriangle className="w-4 h-4 text-red-500" />}
                                {validation.severity === 'warning' && <AlertTriangle className="w-4 h-4 text-yellow-500" />}
                                {validation.severity === 'info' && <CheckCircle className="w-4 h-4 text-blue-500" />}
                                {validation.message}
                              </span>
                            </AlertDescription>
                          </Alert>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* AWS Resources */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">AWS Resources to be Created</h3>
              <div className="bg-gray-50 p-4 rounded-lg space-y-3">
                <div className="space-y-2">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-blue-500 rounded-full"></div>
                    <span className="text-sm font-medium">S3 Bucket</span>
                    <span className="text-xs text-gray-500">({analysis?.repository_name?.toLowerCase().replace(/[^a-z0-9-]/g, '-')}-hosting)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-orange-500 rounded-full"></div>
                    <span className="text-sm font-medium">CloudFront Distribution</span>
                    <span className="text-xs text-gray-500">(Global CDN)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-green-500 rounded-full"></div>
                    <span className="text-sm font-medium">IAM Role & Policy</span>
                    <span className="text-xs text-gray-500">(Deployment permissions)</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-purple-500 rounded-full"></div>
                    <span className="text-sm font-medium">Route 53 (Optional)</span>
                    <span className="text-xs text-gray-500">(Custom domain support)</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Terraform Configuration */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Terraform Configuration</h3>
              <div className="bg-gray-50 p-4 rounded-lg">
                <pre className="text-xs text-gray-700 whitespace-pre-wrap">
{`# Terraform will create:
# - S3 bucket for static hosting
# - CloudFront distribution for global delivery
# - IAM policies for secure access
# - SSL certificate for HTTPS
# - Output: Live website URL

terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

resource "aws_s3_bucket" "website" {
  bucket = "${analysis?.repository_name?.toLowerCase().replace(/[^a-z0-9-]/g, '-')}-hosting"
}

resource "aws_cloudfront_distribution" "website" {
  # Global CDN configuration
}

# Additional resources as needed...`}
                </pre>
              </div>
            </div>

            <div className="flex justify-between">
              <Button variant="outline" onClick={() => setStep(3)}>
                Back to Credentials
              </Button>
              <Button 
                onClick={startDeployment}
                className="bg-blue-600 hover:bg-blue-700"
              >
                Deploy Infrastructure
              </Button>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Step 4: Deployment Progress */}
  {step === 4 && (
        <Card>
          <CardHeader>
    <CardTitle ref={stepHeadingRef as any} tabIndex={-1} className="flex items-center gap-2 focus:outline-none">
              <Clock className="w-5 h-5" />
              Deployment in Progress
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <Alert>
              <Clock className="w-4 h-4" />
              <AlertDescription>
                Your application is being deployed to AWS. This process typically takes 5-15 minutes.
              </AlertDescription>
            </Alert>

            {/* CloudFront Deployment Notice */}
            {(() => {
              const cloudfrontStep = deploymentStatus.find(s => 
                s.step === 'CloudFront Configuration' || 
                s.step.includes('CloudFront')
              );
              const isCloudFrontDeploying = cloudfrontStep?.status === 'running' && 
                (cloudfrontStep?.message?.includes('deploying globally') || 
                 cloudfrontStep?.message?.includes('15-20 minutes'));
              
              if (isCloudFrontDeploying) {
                return (
                  <Alert className="border-blue-200 bg-blue-50">
                    <Globe className="w-4 h-4 text-blue-600" />
                    <AlertDescription className="text-blue-800">
                      <strong>CloudFront Global Deployment in Progress</strong><br/>
                      Your CDN is being deployed to AWS edge locations worldwide. This can take 15-20 minutes 
                      but ensures lightning-fast global access to your website.
                    </AlertDescription>
                  </Alert>
                );
              }
              return null;
            })()}

            {/* Enhanced Progress Overview */}
            <div className="bg-gray-50 rounded-lg p-4 mb-4">
              <div className="flex items-center justify-between mb-2">
                <span className="text-sm font-medium">Deployment Progress</span>
                <span className="text-sm text-gray-500">{Math.round(getOverallProgress())}%</span>
              </div>
              <Progress value={getOverallProgress()} className="h-2 mb-2" />
              <div className="text-xs text-gray-600">
                {deploymentStatus.length > 0 ? (
                  <>
                    {`${deploymentStatus.filter(s => s.status === 'completed').length} of ${Math.max(6, deploymentStatus.length)} steps completed`}
                    {deploymentStatus.filter(s => s.status === 'running').length > 0 && (
                      <span className="text-blue-600 ml-2">
                        • {deploymentStatus.filter(s => s.status === 'running').length} in progress
                      </span>
                    )}
                  </>
                ) : (
                  <span className="text-blue-600">Initializing deployment...</span>
                )}
              </div>
            </div>

            {/* Detailed Step Progress (condensed) */}
            <div className="space-y-3" aria-live="polite" aria-atomic="false">
              {getDeploymentSteps().map((stepInfo, index) => {
                const active = stepInfo.status === 'running' || stepInfo.status === 'failed';
                return (
                  <div key={index} className={`flex items-center gap-3 p-4 bg-white dark:bg-gray-950 border rounded-lg shadow-sm ${!active ? 'py-3' : ''}`}>
                    <div className="flex-shrink-0">
                      {stepInfo.status === 'completed' && (
                        <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center" aria-label="Completed step">
                          <CheckCircle className="w-5 h-5 text-green-600" />
                        </div>
                      )}
                      {stepInfo.status === 'running' && (
                        <div className="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center" aria-label="Step in progress">
                          <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
                        </div>
                      )}
                      {stepInfo.status === 'failed' && (
                        <div className="w-8 h-8 bg-red-100 rounded-full flex items-center justify-center" aria-label="Step failed">
                          <AlertTriangle className="w-5 h-5 text-red-600" />
                        </div>
                      )}
                      {stepInfo.status === 'pending' && (
                        <div className="w-8 h-8 bg-gray-100 rounded-full flex items-center justify-center" aria-label="Pending step">
                          <Clock className="w-5 h-5 text-gray-400" />
                        </div>
                      )}
                    </div>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-lg flex items-center justify-center" aria-hidden="true">{stepInfo.icon}</span>
                        <h4 className="font-medium text-gray-900 truncate">{stepInfo.name}</h4>
                        <Badge 
                          variant={stepInfo.status === 'completed' ? 'default' : 
                                  stepInfo.status === 'running' ? 'secondary' : 
                                  stepInfo.status === 'failed' ? 'destructive' : 'outline'}
                          className="text-xs"
                        >
                          {stepInfo.status === 'pending' ? 'Waiting' : 
                           stepInfo.status === 'running' ? 'In Progress' :
                           stepInfo.status === 'completed' ? 'Complete' : 'Failed'}
                        </Badge>
                      </div>
                      <p className="text-sm text-gray-600 line-clamp-2">{stepInfo.message}</p>
                      {active && (
                        <div className="mt-2">
                          <Progress 
                            value={stepInfo.name === 'Infrastructure Setup' ? 70 :
                                   stepInfo.name === 'File Upload' ? 85 :
                                   stepInfo.name === 'CloudFront Distribution' ? 40 :
                                   stepInfo.name === 'Security Configuration' ? 75 :
                                   stepInfo.name === 'Final Verification' ? 90 : 50} 
                            className="h-1" 
                          />
                          <div className="text-xs text-blue-600 mt-1">
                            {stepInfo.name === 'Infrastructure Setup' && 'Creating S3 bucket and configuring hosting...'}
                            {stepInfo.name === 'File Upload' && 'Uploading website files to AWS S3...'}
                            {stepInfo.name === 'CloudFront Distribution' && 'Deploying to global edge locations...'}
                            {stepInfo.name === 'Security Configuration' && 'Enabling HTTPS and security policies...'}
                            {stepInfo.name === 'Final Verification' && 'Testing website accessibility...'}
                            {stepInfo.name === 'Deployment Complete' && 'All done! Your site is live!'}
                          </div>
                        </div>
                      )}
                      {stepInfo.logs && stepInfo.logs.length > 0 && active && (
                        <details className="mt-2">
                          <summary className="text-sm text-blue-600 cursor-pointer hover:text-blue-800">View detailed logs</summary>
                          <pre className="text-xs bg-gray-900 text-green-400 p-3 rounded mt-2 overflow-x-auto max-h-32 overflow-y-auto">
                            {stepInfo.logs.join('\n')}
                          </pre>
                        </details>
                      )}
                    </div>
                    {stepInfo.timestamp && (
                      <div className="text-xs text-gray-500 flex-shrink-0">
                        {new Date(stepInfo.timestamp).toLocaleTimeString()}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>


          </CardContent>
        </Card>
      )}

      {/* Step 5: Deployment Complete - Enhanced Beautiful Success Page */}
  {step === 5 && (
        <div className="space-y-6">
          {/* Success Header */}
          <Card className="border-green-200 bg-gradient-to-br from-green-50 to-emerald-50">
            <CardContent className="pt-6">
              <ResultHeader
                variant="success"
                title="Deployment Successful"
                subtitle="Your application is live. CloudFront may take a few minutes to fully propagate globally."
                icon={<CheckCircle className="h-8 w-8 text-green-600" />}
              />
              {deploymentUrl && (
                <div className="bg-white border border-green-200 rounded-lg p-6 max-w-2xl mx-auto">
                    <div className="flex items-center justify-center gap-2 mb-4">
                      <Globe className="w-5 h-5 text-blue-600" />
                      <span className="text-sm font-medium text-gray-700">Live Application URL</span>
                    </div>
                    
                    <div className="flex items-center gap-3 mb-4">
                      <Input 
                        value={deploymentUrl} 
                        readOnly 
                        className="text-center font-mono text-sm bg-gray-50 border-gray-200"
                      />
                      <Button
                        size="sm"
                        variant="outline"
                        onClick={() => navigator.clipboard.writeText(deploymentUrl)}
                        className="text-xs"
                      >
                        Copy
                      </Button>
                    </div>

                    <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
                      <div className="flex items-start gap-2">
                        <Clock className="w-5 h-5 text-blue-600 mt-0.5" />
                        <div>
                          <p className="text-sm font-medium text-blue-800">
                            CloudFront Global Propagation
                          </p>
                          <p className="text-sm text-blue-700 mt-1">
                            Your site is being deployed to AWS edge locations worldwide. 
                            It may take 5-15 minutes to be fully accessible globally. 
                            Keep checking the URL above - it will be live shortly!
                          </p>
                        </div>
                      </div>
                    </div>

                    <div className="flex gap-3 justify-center">
                      <Button onClick={() => window.open(deploymentUrl, '_blank')} className="bg-blue-600 hover:bg-blue-700">
                        <ExternalLink className="w-4 h-4 mr-2" />Check Your Site
                      </Button>
                      <Button variant="outline" onClick={() => setStep(1)} className="border-gray-300">Deploy Another Project</Button>
                    </div>
                  </div>
              )}
            </CardContent>
          </Card>

          {/* Deployment Summary */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Settings className="w-5 h-5 text-blue-600" />
                Deployment Summary
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Project Information */}
                <div className="space-y-3" aria-live="polite" aria-atomic="false">
                  <h3 className="font-semibold text-gray-900 border-b pb-2">Project Details</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Repository:</span>
                      <span className="font-medium">{analysis?.repository_name || 'cv-site'}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Framework:</span>
                      <Badge variant="outline" className="text-xs">
                        {analysis?.framework || analysis?.detected_framework || 'Static HTML'}
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Project Type:</span>
                      <span className="font-medium">
                        {isStaticSite(analysis) ? 'Static Website' : 'Web Application'}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Deployment ID:</span>
                      <code className="text-xs bg-gray-100 px-2 py-1 rounded">{deploymentId}</code>
                    </div>
                  </div>
                </div>

                {/* Infrastructure Information */}
                <div className="space-y-3">
                  <h3 className="font-semibold text-gray-900 border-b pb-2">AWS Infrastructure</h3>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-gray-600">Storage:</span>
                      <span className="font-medium">Amazon S3</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">CDN:</span>
                      <span className="font-medium">CloudFront Global</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">SSL/TLS:</span>
                      <Badge variant="outline" className="text-xs bg-green-50 text-green-700 border-green-200">
                        Enabled (HTTPS)
                      </Badge>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-gray-600">Region:</span>
                      <span className="font-medium">{awsCredentials?.region || 'us-east-1'}</span>
                    </div>
                  </div>
                </div>
              </div>

              <Separator className="my-6" />

              {/* Performance Features */}
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                  <Zap className="w-4 h-4 text-yellow-500" />
                  Performance Features
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Global CDN Distribution</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Automatic Compression</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>Edge Caching</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>HTTP/2 Support</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>SSL/TLS Encryption</span>
                  </div>
                  <div className="flex items-center gap-2 text-sm">
                    <CheckCircle className="w-4 h-4 text-green-500" />
                    <span>99.99% Uptime SLA</span>
                  </div>
                </div>
              </div>

              <Separator className="my-6" />

              {/* Next Steps */}
              <div className="space-y-3">
                <h3 className="font-semibold text-gray-900">What's Next?</h3>
                <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                  <ul className="space-y-2 text-sm text-blue-800">
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-0.5">•</span>
                      <span>Your site is now accessible globally with fast loading times</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-0.5">•</span>
                      <span>CloudFront provides automatic HTTPS and DDoS protection</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-0.5">•</span>
                      <span>Update your repository to automatically redeploy changes</span>
                    </li>
                    <li className="flex items-start gap-2">
                      <span className="text-blue-600 mt-0.5">•</span>
                      <span>Monitor performance and usage through AWS console</span>
                    </li>
                  </ul>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Step 6: Deployment Failed */}
  {step === 6 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              Deployment Failed
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <ResultHeader
              variant="error"
              title="Deployment Failed"
              subtitle="Check the logs below, adjust your repository or credentials, and retry."
              icon={<AlertTriangle className="h-8 w-8 text-red-600" />}
            />

            {deploymentId && (
              <div className="bg-gray-50 p-4 rounded-lg">
                <Label className="text-sm text-gray-600">Deployment ID</Label>
                <code className="block bg-white px-3 py-2 rounded border mt-1 text-sm font-mono">
                  {deploymentId}
                </code>
              </div>
            )}

            <div className="flex gap-3 justify-center">
              <Button variant="outline" onClick={() => setStep(1)} className="border-red-300 text-red-700 hover:bg-red-50">
                <ArrowRight className="w-4 h-4 mr-2 rotate-180" />Back to Analysis
              </Button>
              <Button onClick={() => setStep(3)} className="bg-blue-600 hover:bg-blue-700">Try Again</Button>
            </div>

            <div className="text-center text-sm text-gray-600">
              <p>
                If the issue persists, please check your AWS credentials and repository configuration.
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default DeploymentFlow;
