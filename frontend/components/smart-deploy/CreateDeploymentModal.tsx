// Create Deployment Modal - Form for setting up new Smart Deployments
'use client';

import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Switch } from '@/components/ui/switch';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
  Github, 
  Cloud, 
  Settings, 
  Zap, 
  Globe,
  Server,
  Database,
  Shield,
  Loader2
} from 'lucide-react';

interface CloudProvider {
  id: string;
  name: string;
  description: string;
  supported_features: string[];
}

interface ProjectType {
  id: string;
  name: string;
  description: string;
}

interface CreateDeploymentModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: any) => Promise<void>;
  analysisResult?: any;
}

export function CreateDeploymentModal({ isOpen, onClose, onSubmit, analysisResult }: CreateDeploymentModalProps) {
  const [activeTab, setActiveTab] = useState('basic');
  const [isLoading, setIsLoading] = useState(false);
  const [providers, setProviders] = useState<CloudProvider[]>([]);
  const [projectTypes, setProjectTypes] = useState<ProjectType[]>([]);
  
  // Form state
  const [formData, setFormData] = useState({
    project_name: '',
    cloud_provider: 'aws',
    environment: 'production',
    domain_name: '',
    github_repo: '',
    auto_deploy: false,
    framework_type: 'auto-detect', // Add framework selection
    // Advanced options
    enable_monitoring: true,
    enable_cdn: true,
    enable_ssl: true,
    instance_type: 't3.micro',
    auto_scaling: false,
    backup_enabled: true,
    custom_vpc: false
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  // Fetch supported providers and project types
  useEffect(() => {
    if (isOpen) {
      fetchProviders();
      fetchProjectTypes();
    }
  }, [isOpen]);

  const fetchProviders = async () => {
    try {
      const response = await fetch('/api/v1/smart-deploy/providers');
      if (response.ok) {
        const data = await response.json();
        setProviders(data.providers || []);
      }
    } catch (error) {
      console.error('Failed to fetch providers:', error);
    }
  };

  const fetchProjectTypes = async () => {
    try {
      const response = await fetch('/api/v1/smart-deploy/project-types');
      if (response.ok) {
        const data = await response.json();
        setProjectTypes(data.project_types || []);
      }
    } catch (error) {
      console.error('Failed to fetch project types:', error);
    }
  };

  const validateForm = () => {
    const newErrors: Record<string, string> = {};

    if (!formData.project_name.trim()) {
      newErrors.project_name = 'Project name is required';
    } else if (formData.project_name.length < 3) {
      newErrors.project_name = 'Project name must be at least 3 characters';
    } else if (!/^[a-zA-Z0-9-_]+$/.test(formData.project_name)) {
      newErrors.project_name = 'Project name can only contain letters, numbers, hyphens, and underscores';
    }

    if (formData.github_repo && !formData.github_repo.includes('github.com')) {
      newErrors.github_repo = 'Please enter a valid GitHub repository URL';
    }

    if (formData.domain_name && !/^[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/.test(formData.domain_name)) {
      newErrors.domain_name = 'Please enter a valid domain name';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }

    setIsLoading(true);
    try {
      // Include analysis result in the deployment data
      const deploymentData = {
        ...formData,
        // Add framework and analysis information
        // Use manual framework selection if no analysis result
        framework: analysisResult?.framework || analysisResult?.projectType || 
                  (formData.framework_type !== 'auto-detect' ? formData.framework_type : null),
        framework_type: analysisResult?.framework?.type || formData.framework_type,
        project_type: analysisResult?.projectType || analysisResult?.project_type || 
                     (formData.framework_type !== 'auto-detect' ? formData.framework_type : null),
        analysis_result: analysisResult || null
      };
      
      await onSubmit(deploymentData);
      // Reset form
      setFormData({
        project_name: '',
        cloud_provider: 'aws',
        environment: 'production',
        domain_name: '',
        github_repo: '',
        auto_deploy: false,
        framework_type: 'auto-detect',
        enable_monitoring: true,
        enable_cdn: true,
        enable_ssl: true,
        instance_type: 't3.micro',
        auto_scaling: false,
        backup_enabled: true,
        custom_vpc: false
      });
      setErrors({});
    } catch (error) {
      console.error('Failed to create deployment:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
    // Clear error when user starts typing
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: '' }));
    }
  };

  const getProviderIcon = (providerId: string) => {
    switch (providerId) {
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

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-blue-500" />
            Create Smart Deployment
          </DialogTitle>
          <DialogDescription>
            Configure your Terraform-based infrastructure deployment. Smart Deploy will analyze your project and select optimal cloud infrastructure templates.
          </DialogDescription>
        </DialogHeader>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="basic">Basic Configuration</TabsTrigger>
            <TabsTrigger value="infrastructure">Infrastructure</TabsTrigger>
            <TabsTrigger value="advanced">Advanced Options</TabsTrigger>
          </TabsList>

          <TabsContent value="basic" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Settings className="h-4 w-4" />
                  Project Details
                </CardTitle>
                <CardDescription>
                  Basic information about your project and deployment
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="project_name">Project Name *</Label>
                    <Input
                      id="project_name"
                      placeholder="my-awesome-app"
                      value={formData.project_name}
                      onChange={(e) => handleInputChange('project_name', e.target.value)}
                      className={errors.project_name ? 'border-red-500' : ''}
                    />
                    {errors.project_name && (
                      <p className="text-sm text-red-500">{errors.project_name}</p>
                    )}
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="environment">Environment</Label>
                    <Select
                      value={formData.environment}
                      onValueChange={(value) => handleInputChange('environment', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="development">
                          <div className="flex items-center gap-2">
                            <Badge className={getEnvironmentColor('development')}>Development</Badge>
                          </div>
                        </SelectItem>
                        <SelectItem value="staging">
                          <div className="flex items-center gap-2">
                            <Badge className={getEnvironmentColor('staging')}>Staging</Badge>
                          </div>
                        </SelectItem>
                        <SelectItem value="production">
                          <div className="flex items-center gap-2">
                            <Badge className={getEnvironmentColor('production')}>Production</Badge>
                          </div>
                        </SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="framework_type" className="flex items-center gap-2">
                    <Server className="h-4 w-4" />
                    Framework Type
                  </Label>
                  <Select
                    value={formData.framework_type}
                    onValueChange={(value) => handleInputChange('framework_type', value)}
                  >
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="auto-detect">
                        <div className="flex items-center gap-2">
                          <Zap className="h-4 w-4" />
                          Auto-detect from repository
                        </div>
                      </SelectItem>
                      <SelectItem value="react">
                        <div className="flex items-center gap-2">
                          <Cloud className="h-4 w-4" />
                          React SPA (→ CloudFront + S3)
                        </div>
                      </SelectItem>
                      <SelectItem value="static">
                        <div className="flex items-center gap-2">
                          <Cloud className="h-4 w-4" />
                          Static Website (→ CloudFront + S3)
                        </div>
                      </SelectItem>
                    </SelectContent>
                  </Select>
                  <p className="text-sm text-gray-600">
                    {formData.framework_type === 'auto-detect' 
                      ? 'Framework will be detected from your GitHub repository' 
                      : '☁️ Static/SPA frameworks deploy to CloudFront + S3'
                    }
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="github_repo" className="flex items-center gap-2">
                    <Github className="h-4 w-4" />
                    GitHub Repository (Optional)
                  </Label>
                  <Input
                    id="github_repo"
                    placeholder="https://github.com/username/repository"
                    value={formData.github_repo}
                    onChange={(e) => handleInputChange('github_repo', e.target.value)}
                    className={errors.github_repo ? 'border-red-500' : ''}
                  />
                  {errors.github_repo && (
                    <p className="text-sm text-red-500">{errors.github_repo}</p>
                  )}
                  <p className="text-sm text-gray-600">
                    If provided, Smart Deploy will analyze your repository for optimal infrastructure template selection
                  </p>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="domain_name" className="flex items-center gap-2">
                    <Globe className="h-4 w-4" />
                    Custom Domain (Optional)
                  </Label>
                  <Input
                    id="domain_name"
                    placeholder="myapp.com"
                    value={formData.domain_name}
                    onChange={(e) => handleInputChange('domain_name', e.target.value)}
                    className={errors.domain_name ? 'border-red-500' : ''}
                  />
                  {errors.domain_name && (
                    <p className="text-sm text-red-500">{errors.domain_name}</p>
                  )}
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="infrastructure" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Cloud className="h-4 w-4" />
                  Cloud Provider
                </CardTitle>
                <CardDescription>
                  Choose your preferred cloud platform for deployment
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {providers.map((provider) => (
                    <div
                      key={provider.id}
                      className={`p-4 border rounded-lg cursor-pointer transition-all ${
                        formData.cloud_provider === provider.id
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleInputChange('cloud_provider', provider.id)}
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <span className="text-2xl">{getProviderIcon(provider.id)}</span>
                        <h3 className="font-medium">{provider.name}</h3>
                      </div>
                      <p className="text-sm text-gray-600 mb-3">{provider.description}</p>
                      <div className="flex flex-wrap gap-1">
                        {provider.supported_features.slice(0, 3).map((feature) => (
                          <Badge key={feature} variant="secondary" className="text-xs">
                            {feature.replace('_', ' ')}
                          </Badge>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Infrastructure Features</CardTitle>
                <CardDescription>
                  Configure the infrastructure components for your deployment
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-6">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="flex items-center gap-2">
                        <Shield className="h-4 w-4" />
                        SSL Certificate
                      </Label>
                      <p className="text-sm text-gray-600">Enable HTTPS with automatic SSL</p>
                    </div>
                    <Switch
                      checked={formData.enable_ssl}
                      onCheckedChange={(checked: boolean) => handleInputChange('enable_ssl', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Content Delivery Network</Label>
                      <p className="text-sm text-gray-600">Global CDN for faster content delivery</p>
                    </div>
                    <Switch
                      checked={formData.enable_cdn}
                      onCheckedChange={(checked: boolean) => handleInputChange('enable_cdn', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="flex items-center gap-2">
                        <Server className="h-4 w-4" />
                        Monitoring
                      </Label>
                      <p className="text-sm text-gray-600">Real-time application monitoring</p>
                    </div>
                    <Switch
                      checked={formData.enable_monitoring}
                      onCheckedChange={(checked: boolean) => handleInputChange('enable_monitoring', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label className="flex items-center gap-2">
                        <Database className="h-4 w-4" />
                        Automated Backups
                      </Label>
                      <p className="text-sm text-gray-600">Daily automated data backups</p>
                    </div>
                    <Switch
                      checked={formData.backup_enabled}
                      onCheckedChange={(checked: boolean) => handleInputChange('backup_enabled', checked)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="advanced" className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Advanced Configuration</CardTitle>
                <CardDescription>
                  Fine-tune your deployment with advanced options
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="instance_type">Instance Type</Label>
                    <Select
                      value={formData.instance_type}
                      onValueChange={(value) => handleInputChange('instance_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="t3.micro">t3.micro (1 vCPU, 1GB RAM) - $8/month</SelectItem>
                        <SelectItem value="t3.small">t3.small (2 vCPU, 2GB RAM) - $16/month</SelectItem>
                        <SelectItem value="t3.medium">t3.medium (2 vCPU, 4GB RAM) - $33/month</SelectItem>
                        <SelectItem value="t3.large">t3.large (2 vCPU, 8GB RAM) - $67/month</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Auto Scaling</Label>
                      <p className="text-sm text-gray-600">Automatically scale based on traffic</p>
                    </div>
                    <Switch
                      checked={formData.auto_scaling}
                      onCheckedChange={(checked: boolean) => handleInputChange('auto_scaling', checked)}
                    />
                  </div>
                </div>

                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Custom VPC</Label>
                      <p className="text-sm text-gray-600">Deploy in a custom Virtual Private Cloud</p>
                    </div>
                    <Switch
                      checked={formData.custom_vpc}
                      onCheckedChange={(checked: boolean) => handleInputChange('custom_vpc', checked)}
                    />
                  </div>

                  <div className="flex items-center justify-between">
                    <div className="space-y-0.5">
                      <Label>Auto Deploy</Label>
                      <p className="text-sm text-gray-600">Automatically deploy after infrastructure generation</p>
                    </div>
                    <Switch
                      checked={formData.auto_deploy}
                      onCheckedChange={(checked: boolean) => handleInputChange('auto_deploy', checked)}
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>

        <DialogFooter className="flex gap-3">
          <Button variant="outline" onClick={onClose} disabled={isLoading}>
            Cancel
          </Button>
          <Button onClick={handleSubmit} disabled={isLoading} className="min-w-[120px]">
            {isLoading ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Creating...
              </>
            ) : (
              <>
                <Zap className="h-4 w-4 mr-2" />
                Create Deployment
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
