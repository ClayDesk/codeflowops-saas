// Infrastructure Preview - Visual preview of infrastructure templates before deployment
'use client';

import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { 
  Cloud, 
  Server, 
  Database, 
  Globe, 
  Shield, 
  BarChart3,
  Download,
  Eye,
  RefreshCw,
  Zap,
  DollarSign,
  Clock
} from 'lucide-react';

interface InfrastructureResource {
  id: string;
  name: string;
  type: string;
  description: string;
  estimated_cost: number;
  dependencies: string[];
}

interface InfrastructurePreview {
  cloud_provider: string;
  project_type: string;
  resources: InfrastructureResource[];
  estimated_monthly_cost: number;
  deployment_time: string;
}

export function InfrastructurePreview() {
  const [selectedProvider, setSelectedProvider] = useState('aws');
  const [selectedProjectType, setSelectedProjectType] = useState('static_site');
  const [preview, setPreview] = useState<InfrastructurePreview | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('visual');

  const cloudProviders = [
    { id: 'aws', name: 'Amazon Web Services', icon: '🌩️' },
    { id: 'gcp', name: 'Google Cloud Platform', icon: '☁️' },
    { id: 'azure', name: 'Microsoft Azure', icon: '🔷' }
  ];

  const projectTypes = [
    { id: 'static_site', name: 'Static Website' },
    { id: 'spa', name: 'Single Page Application' },
    { id: 'api', name: 'REST API' },
    { id: 'fullstack', name: 'Full-stack Application' },
    { id: 'microservices', name: 'Microservices' }
  ];

  useEffect(() => {
    fetchPreview();
  }, [selectedProvider, selectedProjectType]);

  const fetchPreview = async () => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/smart-deploy/infrastructure/preview', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          cloud_provider: selectedProvider,
          project_type: selectedProjectType
        })
      });

      if (response.ok) {
        const data = await response.json();
        // Mock preview data for demo
        setPreview(generateMockPreview(selectedProvider, selectedProjectType));
      }
    } catch (error) {
      console.error('Failed to fetch preview:', error);
      // Generate mock data on error
      setPreview(generateMockPreview(selectedProvider, selectedProjectType));
    } finally {
      setIsLoading(false);
    }
  };

  const generateMockPreview = (provider: string, projectType: string): InfrastructurePreview => {
    const baseResources: Record<string, InfrastructureResource[]> = {
      static_site: [
        {
          id: 'cdn',
          name: 'CloudFront Distribution',
          type: 'CDN',
          description: 'Global content delivery network for fast loading',
          estimated_cost: 2.50,
          dependencies: []
        },
        {
          id: 'storage',
          name: 'S3 Bucket',
          type: 'Storage',
          description: 'Object storage for static assets',
          estimated_cost: 1.00,
          dependencies: []
        },
        {
          id: 'ssl',
          name: 'SSL Certificate',
          type: 'Security',
          description: 'Free SSL/TLS certificate for HTTPS',
          estimated_cost: 0.00,
          dependencies: ['cdn']
        }
      ],
      spa: [
        {
          id: 'hosting',
          name: 'App Service',
          type: 'Compute',
          description: 'Managed hosting platform',
          estimated_cost: 15.00,
          dependencies: []
        },
        {
          id: 'cdn',
          name: 'CDN',
          type: 'CDN',
          description: 'Content delivery network',
          estimated_cost: 3.00,
          dependencies: ['hosting']
        },
        {
          id: 'monitoring',
          name: 'Application Insights',
          type: 'Monitoring',
          description: 'Performance and error monitoring',
          estimated_cost: 2.50,
          dependencies: ['hosting']
        }
      ],
      api: [
        {
          id: 'compute',
          name: 'Container Service',
          type: 'Compute',
          description: 'Scalable API hosting',
          estimated_cost: 25.00,
          dependencies: []
        },
        {
          id: 'database',
          name: 'Managed Database',
          type: 'Database',
          description: 'PostgreSQL database instance',
          estimated_cost: 20.00,
          dependencies: []
        },
        {
          id: 'loadbalancer',
          name: 'Load Balancer',
          type: 'Networking',
          description: 'Distribute traffic across instances',
          estimated_cost: 18.00,
          dependencies: ['compute']
        },
        {
          id: 'cache',
          name: 'Redis Cache',
          type: 'Cache',
          description: 'In-memory caching layer',
          estimated_cost: 12.00,
          dependencies: ['compute']
        }
      ]
    };

    const resources = baseResources[projectType] || baseResources.static_site;
    const totalCost = resources.reduce((sum, resource) => sum + resource.estimated_cost, 0);

    return {
      cloud_provider: provider,
      project_type: projectType,
      resources,
      estimated_monthly_cost: totalCost,
      deployment_time: '3-5 minutes'
    };
  };

  const getResourceIcon = (type: string) => {
    switch (type) {
      case 'CDN': return <Globe className="h-5 w-5 text-blue-500" />;
      case 'Storage': return <Database className="h-5 w-5 text-green-500" />;
      case 'Security': return <Shield className="h-5 w-5 text-red-500" />;
      case 'Compute': return <Server className="h-5 w-5 text-purple-500" />;
      case 'Database': return <Database className="h-5 w-5 text-orange-500" />;
      case 'Networking': return <Cloud className="h-5 w-5 text-indigo-500" />;
      case 'Cache': return <Zap className="h-5 w-5 text-yellow-500" />;
      case 'Monitoring': return <BarChart3 className="h-5 w-5 text-pink-500" />;
      default: return <Server className="h-5 w-5 text-gray-500" />;
    }
  };

  const getResourceTypeColor = (type: string) => {
    switch (type) {
      case 'CDN': return 'bg-blue-100 text-blue-800';
      case 'Storage': return 'bg-green-100 text-green-800';
      case 'Security': return 'bg-red-100 text-red-800';
      case 'Compute': return 'bg-purple-100 text-purple-800';
      case 'Database': return 'bg-orange-100 text-orange-800';
      case 'Networking': return 'bg-indigo-100 text-indigo-800';
      case 'Cache': return 'bg-yellow-100 text-yellow-800';
      case 'Monitoring': return 'bg-pink-100 text-pink-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const generateInfrastructureCode = () => {
    if (!preview) return '';

    // Generate mock CloudFormation/Terraform code
    const template = {
      AWSTemplateFormatVersion: '2010-09-09',
      Description: `Infrastructure for ${selectedProjectType} on ${selectedProvider.toUpperCase()}`,
      Resources: {}
    };

    preview.resources.forEach(resource => {
      (template.Resources as any)[resource.id] = {
        Type: `AWS::${resource.type}::Resource`,
        Properties: {
          Name: resource.name,
          Description: resource.description
        }
      };
    });

    return JSON.stringify(template, null, 2);
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[400px]">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin mx-auto mb-4 text-blue-500" />
          <p className="text-lg font-medium">Generating Infrastructure Preview...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Eye className="h-5 w-5 text-blue-500" />
            Infrastructure Preview
          </CardTitle>
          <CardDescription>
            Preview the infrastructure that will be generated for your project
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-2">
              <label className="text-sm font-medium">Cloud Provider</label>
              <Select value={selectedProvider} onValueChange={setSelectedProvider}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {cloudProviders.map(provider => (
                    <SelectItem key={provider.id} value={provider.id}>
                      <div className="flex items-center gap-2">
                        <span>{provider.icon}</span>
                        <span>{provider.name}</span>
                      </div>
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <label className="text-sm font-medium">Project Type</label>
              <Select value={selectedProjectType} onValueChange={setSelectedProjectType}>
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {projectTypes.map(type => (
                    <SelectItem key={type.id} value={type.id}>
                      {type.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          </div>

          <div className="flex gap-3 mt-4">
            <Button onClick={fetchPreview} className="flex items-center gap-2">
              <RefreshCw className="h-4 w-4" />
              Regenerate Preview
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="h-4 w-4" />
              Export Template
            </Button>
          </div>
        </CardContent>
      </Card>

      {preview && (
        <>
          {/* Summary */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Estimated Monthly Cost</p>
                    <p className="text-2xl font-bold text-green-600">
                      ${preview.estimated_monthly_cost.toFixed(2)}
                    </p>
                  </div>
                  <DollarSign className="h-8 w-8 text-green-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Resources</p>
                    <p className="text-2xl font-bold text-blue-600">{preview.resources.length}</p>
                  </div>
                  <Server className="h-8 w-8 text-blue-500" />
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardContent className="p-6">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm font-medium text-gray-600">Deployment Time</p>
                    <p className="text-2xl font-bold text-purple-600">{preview.deployment_time}</p>
                  </div>
                  <Clock className="h-8 w-8 text-purple-500" />
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Detailed Preview */}
          <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="visual">Visual Preview</TabsTrigger>
              <TabsTrigger value="code">Infrastructure Code</TabsTrigger>
            </TabsList>

            <TabsContent value="visual">
              <Card>
                <CardHeader>
                  <CardTitle>Infrastructure Resources</CardTitle>
                  <CardDescription>
                    Resources that will be created for your {selectedProjectType} on {selectedProvider.toUpperCase()}
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {preview.resources.map((resource) => (
                      <Card key={resource.id} className="border-2 hover:border-blue-300 transition-colors">
                        <CardContent className="p-4">
                          <div className="flex items-start gap-3 mb-3">
                            {getResourceIcon(resource.type)}
                            <div className="flex-1">
                              <h4 className="font-medium text-sm">{resource.name}</h4>
                              <Badge className={getResourceTypeColor(resource.type)}>
                                {resource.type}
                              </Badge>
                            </div>
                          </div>
                          
                          <p className="text-sm text-gray-600 mb-3">{resource.description}</p>
                          
                          <div className="flex items-center justify-between text-sm">
                            <span className="font-medium">
                              ${resource.estimated_cost.toFixed(2)}/month
                            </span>
                            {resource.dependencies.length > 0 && (
                              <Badge variant="outline" className="text-xs">
                                {resource.dependencies.length} deps
                              </Badge>
                            )}
                          </div>

                          {resource.dependencies.length > 0 && (
                            <div className="mt-2 pt-2 border-t">
                              <p className="text-xs text-gray-500">Dependencies:</p>
                              <div className="flex flex-wrap gap-1 mt-1">
                                {resource.dependencies.map(dep => (
                                  <Badge key={dep} variant="secondary" className="text-xs">
                                    {dep}
                                  </Badge>
                                ))}
                              </div>
                            </div>
                          )}
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </TabsContent>

            <TabsContent value="code">
              <Card>
                <CardHeader>
                  <CardTitle>Infrastructure as Code</CardTitle>
                  <CardDescription>
                    Generated CloudFormation template for your infrastructure
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto">
                    <pre className="text-sm">
                      <code>{generateInfrastructureCode()}</code>
                    </pre>
                  </div>
                  <div className="flex gap-3 mt-4">
                    <Button variant="outline" size="sm" className="flex items-center gap-2">
                      <Download className="h-4 w-4" />
                      Download Template
                    </Button>
                    <Button 
                      variant="outline" 
                      size="sm" 
                      onClick={() => navigator.clipboard.writeText(generateInfrastructureCode())}
                    >
                      Copy to Clipboard
                    </Button>
                  </div>
                </CardContent>
              </Card>
            </TabsContent>
          </Tabs>
        </>
      )}
    </div>
  );
}
