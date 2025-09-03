'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AlertCircle, CheckCircle, Upload, Github, Globe, Rocket, ArrowRight, ArrowLeft } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'

interface DeploymentStep {
  id: string
  title: string
  description: string
  completed: boolean
}

const deploymentSteps: DeploymentStep[] = [
  { id: 'source', title: 'Source', description: 'Choose your code source', completed: false },
  { id: 'template', title: 'Template', description: 'Select deployment template', completed: false },
  { id: 'config', title: 'Configure', description: 'Set up environment', completed: false },
  { id: 'deploy', title: 'Deploy', description: 'Launch your application', completed: false }
]

const templates = [
  {
    id: 'react-spa',
    name: 'React SPA',
    description: 'Single Page Application with React',
    icon: '⚛️',
    features: ['Static hosting', 'CDN distribution', 'Auto-scaling'],
    cost: '$5-15/month',
    deployTime: '2-3 minutes'
  },
  {
    id: 'nodejs-api',
    name: 'Node.js API',
    description: 'RESTful API with Node.js',
    icon: '🟢',
    features: ['Auto-scaling', 'Load balancing', 'Health checks'],
    cost: '$8-20/month',
    deployTime: '2-4 minutes'
  }
]

export function DeploymentWizard() {
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState({
    name: '',
    source: '',
    template: '',
    environment: 'production',
    region: 'us-east-1'
  })
  const [isDeploying, setIsDeploying] = useState(false)
  const [deploymentProgress, setDeploymentProgress] = useState(0)

  const nextStep = () => {
    if (currentStep < deploymentSteps.length - 1) {
      setCurrentStep(currentStep + 1)
    }
  }

  const prevStep = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1)
    }
  }

  const handleDeploy = async () => {
    setIsDeploying(true)
    // Simulate deployment progress
    for (let i = 0; i <= 100; i += 10) {
      await new Promise(resolve => setTimeout(resolve, 200))
      setDeploymentProgress(i)
    }
    setIsDeploying(false)
    // Redirect to deployment details
  }

  const currentStepData = deploymentSteps[currentStep]

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      {/* Header */}
      <div className="text-center space-y-2">
        <h1 className="text-3xl font-bold text-gray-900">Create New Deployment</h1>
        <p className="text-gray-600">Deploy your application in minutes with our guided wizard</p>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-6">
            {deploymentSteps.map((step, index) => (
              <div key={step.id} className="flex items-center">
                <div className={`
                  flex items-center justify-center w-10 h-10 rounded-full border-2 transition-colors
                  ${index <= currentStep 
                    ? 'bg-blue-600 border-blue-600 text-white' 
                    : 'bg-gray-100 border-gray-300 text-gray-400'
                  }
                `}>
                  {index < currentStep ? (
                    <CheckCircle className="h-5 w-5" />
                  ) : (
                    <span className="text-sm font-medium">{index + 1}</span>
                  )}
                </div>
                
                {index < deploymentSteps.length - 1 && (
                  <div className={`
                    w-16 h-0.5 mx-4 transition-colors
                    ${index < currentStep ? 'bg-blue-600' : 'bg-gray-300'}
                  `} />
                )}
              </div>
            ))}
          </div>
          
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900">{currentStepData.title}</h3>
            <p className="text-gray-600">{currentStepData.description}</p>
          </div>
        </CardContent>
      </Card>

      {/* Step Content */}
      <AnimatePresence mode="wait">
        <motion.div
          key={currentStep}
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          exit={{ opacity: 0, x: -20 }}
          transition={{ duration: 0.3 }}
        >
          {currentStep === 0 && <SourceStep formData={formData} setFormData={setFormData} />}
          {currentStep === 1 && <TemplateStep formData={formData} setFormData={setFormData} />}
          {currentStep === 2 && <ConfigureStep formData={formData} setFormData={setFormData} />}
          {currentStep === 3 && (
            <DeployStep 
              formData={formData} 
              isDeploying={isDeploying}
              deploymentProgress={deploymentProgress}
              onDeploy={handleDeploy}
            />
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex justify-between">
        <Button 
          variant="outline" 
          onClick={prevStep} 
          disabled={currentStep === 0}
        >
          <ArrowLeft className="h-4 w-4 mr-2" />
          Previous
        </Button>
        
        {currentStep < deploymentSteps.length - 1 ? (
          <Button onClick={nextStep}>
            Next
            <ArrowRight className="h-4 w-4 ml-2" />
          </Button>
        ) : (
          <Button 
            onClick={handleDeploy} 
            disabled={isDeploying}
            className="bg-green-600 hover:bg-green-700"
          >
            <Rocket className="h-4 w-4 mr-2" />
            {isDeploying ? 'Deploying...' : 'Deploy Now'}
          </Button>
        )}
      </div>
    </div>
  )
}

function SourceStep({ formData, setFormData }: { formData: any; setFormData: any }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Choose Your Source</CardTitle>
        <CardDescription>
          Select where your code is located
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <Tabs defaultValue="github" onValueChange={(value) => setFormData({...formData, source: value})}>
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="github">
              <Github className="h-4 w-4 mr-2" />
              GitHub
            </TabsTrigger>
            <TabsTrigger value="upload">
              <Upload className="h-4 w-4 mr-2" />
              Upload
            </TabsTrigger>
            <TabsTrigger value="template">
              <Globe className="h-4 w-4 mr-2" />
              Template
            </TabsTrigger>
          </TabsList>
          
          <TabsContent value="github" className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="repo">Repository URL</Label>
              <Input
                id="repo"
                placeholder="https://github.com/username/repository"
                value={formData.repoUrl || ''}
                onChange={(e) => setFormData({...formData, repoUrl: e.target.value})}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="branch">Branch</Label>
              <Input
                id="branch"
                placeholder="main"
                value={formData.branch || 'main'}
                onChange={(e) => setFormData({...formData, branch: e.target.value})}
              />
            </div>
          </TabsContent>
          
          <TabsContent value="upload" className="space-y-4">
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Upload className="h-8 w-8 text-gray-400 mx-auto mb-2" />
              <p className="text-gray-600">Drag and drop your files here, or click to browse</p>
              <Button variant="outline" className="mt-2">
                Choose Files
              </Button>
            </div>
          </TabsContent>
          
          <TabsContent value="template" className="space-y-4">
            <p className="text-gray-600">Start with a pre-built template</p>
            <div className="grid grid-cols-2 gap-4">
              {templates.slice(0, 2).map((template) => (
                <div key={template.id} className="border rounded-lg p-4 hover:bg-gray-50 cursor-pointer">
                  <div className="text-2xl mb-2">{template.icon}</div>
                  <h4 className="font-medium">{template.name}</h4>
                  <p className="text-sm text-gray-600">{template.description}</p>
                </div>
              ))}
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}

function TemplateStep({ formData, setFormData }: { formData: any; setFormData: any }) {
  const [selectedTemplate, setSelectedTemplate] = useState('')

  return (
    <Card>
      <CardHeader>
        <CardTitle>Select Template</CardTitle>
        <CardDescription>
          Choose the best template for your application
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {templates.map((template) => (
            <div
              key={template.id}
              className={`
                border-2 rounded-lg p-6 cursor-pointer transition-all hover:shadow-md
                ${selectedTemplate === template.id 
                  ? 'border-blue-500 bg-blue-50' 
                  : 'border-gray-200 hover:border-gray-300'
                }
              `}
              onClick={() => {
                setSelectedTemplate(template.id)
                setFormData({...formData, template: template.id})
              }}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="text-3xl">{template.icon}</div>
                {selectedTemplate === template.id && (
                  <CheckCircle className="h-5 w-5 text-blue-600" />
                )}
              </div>
              
              <h3 className="text-lg font-semibold mb-2">{template.name}</h3>
              <p className="text-gray-600 mb-4">{template.description}</p>
              
              <div className="space-y-3">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Cost:</span>
                  <span className="font-medium">{template.cost}</span>
                </div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-gray-500">Deploy time:</span>
                  <span className="font-medium">{template.deployTime}</span>
                </div>
                
                <div className="space-y-1">
                  <p className="text-sm text-gray-500">Features:</p>
                  <div className="flex flex-wrap gap-1">
                    {template.features.map((feature) => (
                      <Badge key={feature} variant="secondary" className="text-xs">
                        {feature}
                      </Badge>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}

function ConfigureStep({ formData, setFormData }: { formData: any; setFormData: any }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Configure Deployment</CardTitle>
        <CardDescription>
          Set up your application environment and settings
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-2">
            <Label htmlFor="name">Application Name</Label>
            <Input
              id="name"
              placeholder="my-awesome-app"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="environment">Environment</Label>
            <Select value={formData.environment} onValueChange={(value) => setFormData({...formData, environment: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="development">Development</SelectItem>
                <SelectItem value="staging">Staging</SelectItem>
                <SelectItem value="production">Production</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="region">Region</Label>
            <Select value={formData.region} onValueChange={(value) => setFormData({...formData, region: value})}>
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="us-east-1">US East (N. Virginia)</SelectItem>
                <SelectItem value="us-west-2">US West (Oregon)</SelectItem>
                <SelectItem value="eu-west-1">Europe (Ireland)</SelectItem>
                <SelectItem value="ap-southeast-1">Asia Pacific (Singapore)</SelectItem>
              </SelectContent>
            </Select>
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="instances">Instance Count</Label>
            <Select defaultValue="1">
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="1">1 instance</SelectItem>
                <SelectItem value="2">2 instances</SelectItem>
                <SelectItem value="3">3 instances</SelectItem>
                <SelectItem value="auto">Auto-scaling</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
        
        {/* Environment Variables */}
        <div className="space-y-2">
          <Label>Environment Variables</Label>
          <div className="space-y-2">
            <div className="flex gap-2">
              <Input placeholder="VARIABLE_NAME" className="flex-1" />
              <Input placeholder="value" className="flex-1" />
              <Button variant="outline" size="sm">Add</Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

function DeployStep({ formData, isDeploying, deploymentProgress, onDeploy }: { 
  formData: any; 
  isDeploying: boolean; 
  deploymentProgress: number; 
  onDeploy: () => void 
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Ready to Deploy</CardTitle>
        <CardDescription>
          Review your settings and launch your application
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Deployment Summary */}
        <div className="space-y-4">
          <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="font-medium">Application Name</h4>
              <p className="text-sm text-gray-600">{formData.name || 'my-app'}</p>
            </div>
            <Badge variant="secondary">{formData.environment || 'production'}</Badge>
          </div>
          
          <div className="flex justify-between items-center p-4 bg-gray-50 rounded-lg">
            <div>
              <h4 className="font-medium">Template</h4>
              <p className="text-sm text-gray-600">{formData.template || 'react-spa'}</p>
            </div>
            <Badge variant="outline">{formData.region || 'us-east-1'}</Badge>
          </div>
        </div>
        
        {/* Deployment Progress */}
        {isDeploying && (
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold mb-2">Deploying Your Application</h3>
              <p className="text-gray-600">This may take a few minutes...</p>
            </div>
            
            <Progress value={deploymentProgress} className="h-2" />
            
            <div className="text-center text-sm text-gray-600">
              {deploymentProgress < 30 && "Building application..."}
              {deploymentProgress >= 30 && deploymentProgress < 70 && "Deploying to infrastructure..."}
              {deploymentProgress >= 70 && deploymentProgress < 100 && "Running health checks..."}
              {deploymentProgress === 100 && "Deployment complete!"}
            </div>
          </div>
        )}
        
        {/* Estimated Costs */}
        <div className="border rounded-lg p-4">
          <h4 className="font-medium mb-2">Estimated Monthly Cost</h4>
          <div className="space-y-2 text-sm">
            <div className="flex justify-between">
              <span>Compute</span>
              <span>$19.00</span>
            </div>
            <div className="flex justify-between">
              <span>Storage</span>
              <span>$2.50</span>
            </div>
            <div className="flex justify-between">
              <span>Bandwidth</span>
              <span>$1.20</span>
            </div>
            <div className="border-t pt-2 flex justify-between font-medium">
              <span>Total</span>
              <span>$15.70/month</span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
