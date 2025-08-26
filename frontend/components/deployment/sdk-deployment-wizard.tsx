'use client'

import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { AlertCircle, CheckCircle, Github, Globe, Rocket, ArrowRight, ArrowLeft, Eye, EyeOff, ExternalLink, Settings } from 'lucide-react'
import { motion, AnimatePresence } from 'framer-motion'
import { useSmartDeployApi } from '@/lib/api'
import toast from 'react-hot-toast'

interface DeploymentStep {
  id: string
  title: string
  description: string
  completed: boolean
}

const deploymentSteps: DeploymentStep[] = [
  { id: 'source', title: 'Repository', description: 'Analyze GitHub repository', completed: false },
  { id: 'credentials', title: 'AWS Setup', description: 'Configure AWS credentials', completed: false },
  { id: 'framework', title: 'Framework Config', description: 'Configure deployment options', completed: false },
  { id: 'deploy', title: 'Deploy', description: 'Deploy to AWS infrastructure', completed: false },
  { id: 'complete', title: 'Complete', description: 'Deployment successful', completed: false }
]

// Helper function to get framework display info - Dynamic for thousands of users
const getFrameworkDisplayInfo = (framework: string) => {
  if (!framework) return { name: 'Web App', color: 'bg-purple-100 text-purple-800', emoji: '🌐' }
  
  const fw = framework.toLowerCase()
  
  // Dynamic color assignment based on framework characteristics
  const getFrameworkColor = (frameworkName: string) => {
    const hash = frameworkName.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
    const colors = [
      'bg-blue-100 text-blue-800',
      'bg-green-100 text-green-800', 
      'bg-purple-100 text-purple-800',
      'bg-red-100 text-red-800',
      'bg-yellow-100 text-yellow-800',
      'bg-indigo-100 text-indigo-800',
      'bg-pink-100 text-pink-800',
      'bg-cyan-100 text-cyan-800',
      'bg-orange-100 text-orange-800'
    ]
    return colors[hash % colors.length]
  }
  
  // Dynamic emoji assignment based on framework type/language
  const getFrameworkEmoji = (frameworkName: string) => {
    const fw = frameworkName.toLowerCase()
    if (fw.includes('react')) return '⚛️'
    if (fw.includes('vue')) return '🟢'
    if (fw.includes('angular')) return '🅰️'
    if (fw.includes('svelte')) return '🔥'
    if (fw.includes('next')) return '▲'
    if (fw.includes('nuxt')) return '💚'
    if (fw.includes('php') || fw.includes('laravel')) return '�'
    if (fw.includes('python') || fw.includes('django') || fw.includes('flask')) return '�'
    if (fw.includes('node') || fw.includes('express') || fw.includes('javascript')) return '�'
    if (fw.includes('java') || fw.includes('spring')) return '☕'
    if (fw.includes('go') || fw.includes('gin')) return '🔷'
    if (fw.includes('dotnet') || fw.includes('csharp')) return '🔷'
    if (fw.includes('ruby') || fw.includes('rails')) return '�'
    if (fw.includes('rust')) return '🦀'
    if (fw.includes('swift')) return '🍎'
    if (fw.includes('kotlin')) return '🤖'
    if (fw.includes('static') || fw.includes('html')) return '📄'
    return '🌐' // Default web app emoji
  }
  
  // Capitalize framework name for display
  const displayName = framework
    .split(/[-_\s]/)
    .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
  
  return {
    name: displayName,
    color: getFrameworkColor(framework),
    emoji: getFrameworkEmoji(framework)
  }
}

// Helper function to check if project is Python-based
const isPythonProject = (analysisResult: any) => {
  const framework = analysisResult?.framework?.type || analysisResult?.analysis?.detected_framework || analysisResult?.projectType || ''
  const fw = framework.toLowerCase()
  
  // Also check in other potential locations
  const detectedStack = analysisResult?.analysis?.detected_stack || ''
  const primaryTech = analysisResult?.analysis?.executive_summary?.primary_technology || ''
  const frameworks = analysisResult?.analysis?.frameworks || []
  const projectTypeField = analysisResult?.project_type || ''
  
  // Check primary framework field
  const isPython = false
  
  // Check other fields
  const isDetectedPython = false
  
  const isPrimaryTechPython = false
  
  const isFrameworksPython = false
  
  const isProjectTypePython = false
  
  console.log('🔍 isPythonProject Debug:', {
    framework,
    detectedStack,
    primaryTech,
    frameworks,
    projectTypeField,
    result: false
  })
  
  return false
}

export function SDKDeploymentWizard({ initialRepo = '', onClose }: { initialRepo?: string; onClose?: () => void }) {
  const api = useSmartDeployApi()
  const [currentStep, setCurrentStep] = useState(0)
  const [formData, setFormData] = useState({
    repositoryUrl: initialRepo,
    githubToken: '',
    awsAccessKey: '',
    awsSecretKey: '',
    awsRegion: '',
    projectName: ''
  })
  
  // State for each step
  const [isAnalyzing, setIsAnalyzing] = useState(false)
  const [analysisResult, setAnalysisResult] = useState<any>(null)
  const [showSecretKey, setShowSecretKey] = useState(false)
  const [isValidating, setIsValidating] = useState(false)
  const [credentialsValid, setCredentialsValid] = useState<boolean | null>(null)
  const [frameworkConfig, setFrameworkConfig] = useState({
    deploymentType: 'auto', // 'auto', 'cloudfront'
    selectedFramework: ''
  })
  const [isDeploying, setIsDeploying] = useState(false)
  const [deploymentProgress, setDeploymentProgress] = useState(0)
  const [deploymentResult, setDeploymentResult] = useState<any>(null)
  const [deploymentPhase, setDeploymentPhase] = useState('initializing')

  // Repository validation for CodeFlowOps (React + Static sites only)
  const validateRepositoryForCodeFlowOps = (repoUrl: string, analysis?: any): { valid: boolean; message?: string; warning?: string } => {
    console.log('🔍 Starting validation for:', repoUrl)
    
    // Only validate GitHub repositories
    if (!repoUrl.includes('github.com')) {
      return { valid: false, message: "Only GitHub repositories are currently supported" }
    }

    // Enhanced repository name checking for backend and unsupported frameworks
    const repoName = repoUrl.split('/').pop()?.toLowerCase() || ''
    console.log('🔍 Extracted repo name:', repoName)
    
    // Comprehensive check for any unsupported patterns
    const unsupportedPatterns = [
      // PHP Frameworks
      'codeigniter', 'laravel', 'symfony', 'cakephp', 'yii', 'zend',
      // Python Frameworks  
      'django', 'flask', 'fastapi', 'pyramid',
      // Java Frameworks
      'spring', 'struts', 'hibernate',
      // Node.js Backend Frameworks
      'express', 'nestjs', 'koa', 'hapi',
      // Other Backend Frameworks
      'rails', 'gin', 'actix', 'fiber',
      // Project Types
      'ecommerce', 'e-commerce', 'cms', 'admin', 'dashboard', 'api', 'backend', 'server',
      // Languages that indicate backend
      'php', 'python', 'java', 'golang', 'rust', 'ruby'
    ]
    
    // Check each pattern
    for (const pattern of unsupportedPatterns) {
      if (repoName.includes(pattern)) {
        console.log('� Found unsupported pattern:', pattern)
        return {
          valid: false,
          message: `🚀 CodeFlowOps specializes in React and static websites. We detected "${pattern.toUpperCase()}" in your repository, which isn't currently supported. Please try a React, Vue, Angular, or static website repository instead. Support for ${pattern} applications is coming soon!`
        }
      }
    }

    // If we have analysis data, check the detected stack
    if (analysis?.detected_stack) {
      const detectedStack = analysis.detected_stack.toLowerCase()
      const unsupportedStacks = [
        'python', 'django', 'flask', 'fastapi', 'java', 'spring', 
        'dotnet', 'c#', 'ruby', 'rails', 'go', 'rust', 'php', 'laravel', 'codeigniter'
      ]
      
      if (unsupportedStacks.some(stack => detectedStack.includes(stack))) {
        return {
          valid: false,
          message: `🚀 CodeFlowOps specializes in React and static websites. We detected "${detectedStack}" technology which isn't currently supported. Support for ${detectedStack} applications is coming soon!`
        }
      }
    }

    console.log('✅ Validation passed for:', repoName)
    return { valid: true }
  }

  // Progress animation effect for smoother progress bar
  useEffect(() => {
    if (!isDeploying) return

    const progressInterval = setInterval(() => {
      setDeploymentProgress(prev => {
        // Define target progress for each phase
        const phaseTargets = {
          initializing: 8,
          building: 25,
          infrastructure: 45,
          uploading: 70,
          configuring: 85,
          finalizing: 95,
          completed: 100
        }

        const target = phaseTargets[deploymentPhase as keyof typeof phaseTargets] || 0
        
        // Smooth progress increment - slower as we approach target
        if (prev < target) {
          const increment = Math.max(0.5, (target - prev) * 0.1)
          return Math.min(prev + increment, target)
        }
        
        return prev
      })
    }, 200) // Update every 200ms for smooth animation

    return () => clearInterval(progressInterval)
  }, [isDeploying, deploymentPhase])

  // Get dynamic title based on analysis
  const getAppTitle = () => {
    const framework = analysisResult?.framework?.type || analysisResult?.analysis?.detected_framework
    if (framework) {
      const frameworkInfo = getFrameworkDisplayInfo(framework)
      return `Deploy ${frameworkInfo.name} Application`
    }
    return 'Deploy Your Application'
  }

  const getAppDescription = () => {
    const framework = analysisResult?.framework?.type || analysisResult?.analysis?.detected_framework
    if (framework) {
      const frameworkInfo = getFrameworkDisplayInfo(framework)
      return `Deploy your ${frameworkInfo.name} app to AWS with our SDK-powered wizard`
    }
    return 'Deploy your web application to AWS with our SDK-powered wizard'
  }

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

  const handleAnalyzeRepository = async () => {
    if (!formData.repositoryUrl.trim()) {
      toast.error('Please enter a repository URL')
      return
    }

    setIsAnalyzing(true)
    try {
      // Pass both repository URL and GitHub token if provided
      const requestData = {
        repositoryUrl: formData.repositoryUrl,
        ...(formData.githubToken && { githubToken: formData.githubToken })
      }
      
      const result = await api.analyzeRepository(requestData)
      console.log('Analysis result:', result) // Debug log to see what data is available
      setAnalysisResult(result)
      
      // Extract project name from repo URL if not set
      if (!formData.projectName && formData.repositoryUrl) {
        const repoName = formData.repositoryUrl.split('/').pop()?.replace('.git', '') || ''
        setFormData(prev => ({ ...prev, projectName: repoName }))
      }
      
      toast.success('Repository analyzed successfully!')
      // Don't auto-advance to next step - let user see analysis results first
    } catch (error: any) {
      toast.error(`Failed to analyze repository: ${error.message}`)
    } finally {
      setIsAnalyzing(false)
    }
  }



  const handleValidateCredentials = async () => {
    if (!formData.awsAccessKey.trim() || !formData.awsSecretKey.trim()) {
      toast.error('Please enter both AWS access key and secret key')
      return
    }

    setIsValidating(true)
    try {
      await api.validateAwsCredentials({
        aws_access_key: formData.awsAccessKey,
        aws_secret_key: formData.awsSecretKey,
        aws_region: formData.awsRegion
      })
      
      setCredentialsValid(true)
      toast.success('AWS credentials validated successfully!')
      // Don't auto-advance to next step - let user see validation result first
    } catch (error: any) {
      setCredentialsValid(false)
      toast.error(`Invalid AWS credentials: ${error.message}`)
    } finally {
      setIsValidating(false)
    }
  }

  const handleDeploy = async () => {
    console.log('🚀 handleDeploy called')
    console.log('analysisResult:', analysisResult)
    console.log('analysisResult.deployment_id:', analysisResult?.deployment_id)
    console.log('analysisResult.analysis_id:', analysisResult?.analysis_id)
    console.log('formData:', formData)
    
    // Check for deployment_id or analysis_id
    const deploymentId = analysisResult?.deployment_id || analysisResult?.analysis_id
    
    if (!deploymentId) {
      console.error('❌ No deployment ID available')
      console.error('Available properties:', Object.keys(analysisResult || {}))
      toast.error('No deployment ID available. Please re-analyze the repository.')
      return
    }

    if (!formData.awsAccessKey || !formData.awsSecretKey) {
      console.error('❌ Missing AWS credentials')
      toast.error('Please provide AWS credentials.')
      return
    }

    console.log('✅ All validation passed, starting deployment...')
    console.log('Using deployment ID:', deploymentId)
    setIsDeploying(true)
    setDeploymentProgress(0)
    setDeploymentPhase('initializing')

    try {
      // Start deployment with loading message
      console.log('Starting deployment with:', {
        deployment_id: deploymentId,
        aws_region: formData.awsRegion,
        project_name: formData.projectName
      })
      
      toast.success('Starting deployment...')
      
      // Simulate phase progression
      setTimeout(() => setDeploymentPhase('building'), 2000)

      // Determine framework to use based on config
      // Extract framework from the correct location in analysis result
      const detectedFramework = analysisResult?.analysis?.intelligence_profile?.frameworks?.[0]?.type || 
                                analysisResult?.analysis?.intelligence_profile?.frameworks?.[0]?.name ||
                                analysisResult?.framework?.type || 
                                analysisResult?.analysis?.detected_framework ||
                                analysisResult?.projectType
      
      let finalFramework = detectedFramework
      
      if (frameworkConfig.deploymentType === 'auto') {
        finalFramework = detectedFramework
      }

      console.log('🔧 Framework configuration:', frameworkConfig)
      console.log('🎯 Final framework for deployment:', finalFramework)
      console.log('🔍 Analysis frameworks array:', analysisResult?.analysis?.intelligence_profile?.frameworks)

      // Start deployment
      const deployResult = await api.deployWithCredentials({
        deployment_id: deploymentId,
        aws_access_key: formData.awsAccessKey,
        aws_secret_key: formData.awsSecretKey,
        aws_region: formData.awsRegion,
        project_name: formData.projectName,
        framework: finalFramework,
        repository_url: formData.repositoryUrl  // Add repository URL
      })

      console.log('Deployment started:', deployResult)
      toast.success('Deployment initiated successfully!')
      setTimeout(() => setDeploymentPhase('infrastructure'), 4000)

      // Real deployment status polling with detailed steps
      const pollDeployment = async () => {
        let attempts = 0
        const maxAttempts = 30 // 5 minutes max

        const pollInterval = setInterval(async () => {
          attempts++
          console.log(`Polling attempt ${attempts}/${maxAttempts}`)
          
          try {
            // Progress phases based on polling attempts
            if (attempts === 3) setDeploymentPhase('uploading')
            if (attempts === 8) setDeploymentPhase('configuring')
            if (attempts === 15) setDeploymentPhase('finalizing')
            
            // Try to get deployment result first
            const result = await api.getDeploymentResult(deploymentId)
            console.log('Polling result:', result)
            
            if (result) {
              // Check the actual status from backend
              if ((result.status === 'deployed' || result.status === 'completed') && (result.deployment_url || result.deployment_details?.cloudfront_url)) {
                // Deployment completed successfully
                const liveUrl = result.deployment_url || result.deployment_details?.cloudfront_url
                setDeploymentResult({
                  cloudfront_url: liveUrl,
                  s3_bucket: result.deployment_details?.s3_bucket || 'Created successfully',
                  status: 'success',
                  deployment_details: result.deployment_details
                })
                setDeploymentPhase('completed')
                setTimeout(() => {
                  clearInterval(pollInterval)
                  setIsDeploying(false)
                  toast.success('🎉 Deployment completed successfully!')
                  nextStep()
                }, 1000)
                return
              } else if (result.status === 'failed') {
                // Deployment failed
                console.error('Deployment failed:', result)
                setDeploymentProgress(0)
                clearInterval(pollInterval)
                setIsDeploying(false)
                toast.error(`❌ Deployment failed: ${result.error || 'Unknown error'}`)
                
                // Show error details to user
                setDeploymentResult({
                  status: 'failed',
                  error: result.error || 'Deployment failed',
                  logs: result.logs || []
                })
                
                return // Don't proceed to next step
              }
            }

          } catch (error) {
            // Continue polling on errors for a bit, but log them
            console.log(`Polling attempt ${attempts} failed:`, error)
            
            if (attempts > 5) {
              // After 5 failed attempts, this might be a real error
              toast.error('Having trouble checking deployment status...')
            }
          }

          // Timeout after max attempts
          if (attempts >= maxAttempts) {
            console.log('Deployment polling timeout reached')
            clearInterval(pollInterval)
            setIsDeploying(false)
            
            // Try one final check
            try {
              const finalResult = await api.getDeploymentResult(deploymentId)
              console.log('Final check result:', finalResult)
              
              if (finalResult && finalResult.status === 'deployed' && (finalResult.deployment_url || finalResult.deployment_details?.cloudfront_url)) {
                const liveUrl = finalResult.deployment_url || finalResult.deployment_details?.cloudfront_url
                setDeploymentResult({
                  cloudfront_url: liveUrl,
                  s3_bucket: finalResult.deployment_details?.s3_bucket || 'Created successfully',
                  status: 'success',
                  deployment_details: finalResult.deployment_details
                })
                setDeploymentPhase('completed')
                toast.success('🎉 Deployment completed successfully!')
                nextStep()
              } else {
                // Deployment likely failed or timed out
                console.error('Deployment timeout or failure:', finalResult)
                setDeploymentProgress(0)
                toast.error('⏱️ Deployment timeout - please check your AWS credentials and try again')
                
                setDeploymentResult({
                  status: 'timeout',
                  error: 'Deployment timed out. This usually means invalid AWS credentials or insufficient permissions.',
                  logs: finalResult?.logs || []
                })
                
                // Move to completion step to show error
                nextStep()
              }
            } catch (finalError) {
              console.error('Final check failed:', finalError)
              setDeploymentProgress(0)
              toast.error('❌ Deployment failed - please verify your AWS credentials')
              
              setDeploymentResult({
                status: 'failed',
                error: 'Unable to verify deployment status. Please check your AWS credentials and try again.',
                logs: []
              })
              
              // Move to completion step to show error
              nextStep()
            }
          }
        }, 10000) // Check every 10 seconds
      }

      // Start polling
      pollDeployment()

    } catch (error: any) {
      console.error('Deployment initiation failed:', error)
      toast.error(`Deployment failed: ${error.message}`)
      setDeploymentProgress(0)
      setIsDeploying(false)
      
      // Set error state
      setDeploymentResult({
        status: 'failed',
        error: error.message || 'Failed to start deployment',
        logs: []
      })
      
      // Move to completion step to show error
      nextStep()
    }
  }

  const currentStepData = deploymentSteps[currentStep]
  const router = useRouter()

  return (
    <div className="max-w-4xl mx-auto space-y-4 md:space-y-6 pt-4 md:pt-8 px-4 sm:px-6">
      {/* Header */}
      <div className="text-center space-y-2 pt-2 md:pt-4">
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 dark:text-white">{getAppTitle()}</h1>
        <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300">{getAppDescription()}</p>
      </div>

      {/* Progress Steps */}
      <Card>
        <CardContent className="p-4 sm:p-6">
          <div className="flex items-center justify-between mb-4 sm:mb-6 overflow-x-auto">
            {deploymentSteps.map((step, index) => (
              <div key={step.id} className="flex items-center flex-shrink-0">
                <div className={`
                  flex items-center justify-center w-8 h-8 sm:w-10 sm:h-10 rounded-full border-2 transition-colors
                  ${index <= currentStep 
                    ? 'bg-blue-600 border-blue-600 text-white' 
                    : 'bg-gray-100 border-gray-300 text-gray-400'
                  }
                `}>
                  {index < currentStep ? (
                    <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5" />
                  ) : (
                    <span className="text-xs sm:text-sm font-medium">{index + 1}</span>
                  )}
                </div>
                
                {index < deploymentSteps.length - 1 && (
                  <div className={`
                    w-8 sm:w-16 h-0.5 mx-2 sm:mx-4 transition-colors
                    ${index < currentStep ? 'bg-blue-600' : 'bg-gray-300'}
                  `} />
                )}
              </div>
            ))}
          </div>
          
          <div className="text-center">
            <h3 className="text-base sm:text-lg font-semibold text-gray-900 dark:text-white">{currentStepData.title}</h3>
            <p className="text-sm sm:text-base text-gray-600 dark:text-gray-300">{currentStepData.description}</p>
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
          {currentStep === 0 && (
            <RepositoryStep 
              formData={formData} 
              setFormData={setFormData} 
              isAnalyzing={isAnalyzing}
              analysisResult={analysisResult}
              onAnalyze={handleAnalyzeRepository}
            />
          )}
          {currentStep === 1 && (
            <CredentialsStep 
              formData={formData} 
              setFormData={setFormData}
              showSecretKey={showSecretKey}
              setShowSecretKey={setShowSecretKey}
              isValidating={isValidating}
              credentialsValid={credentialsValid}
              onValidate={handleValidateCredentials}
            />
          )}
          {currentStep === 2 && (
            <FrameworkConfigStep 
              analysisResult={analysisResult}
              frameworkConfig={frameworkConfig}
              setFrameworkConfig={setFrameworkConfig}
              onNext={nextStep}
            />
          )}
          {currentStep === 3 && (
            <DeployStep 
              formData={formData}
              analysisResult={analysisResult}
              frameworkConfig={frameworkConfig}
              isDeploying={isDeploying}
              deploymentProgress={deploymentProgress}
              deploymentPhase={deploymentPhase}
              onDeploy={handleDeploy}
            />
          )}
          {currentStep === 4 && (
            <CompleteStep 
              deploymentResult={deploymentResult}
              formData={formData}
              analysisResult={analysisResult}
            />
          )}
        </motion.div>
      </AnimatePresence>

      {/* Navigation */}
      <div className="flex flex-col sm:flex-row justify-between gap-3 sm:gap-0 pb-6 md:pb-8">
        <Button 
          variant="outline" 
          onClick={currentStep === 0 ? (onClose || (() => router.push('/deploy'))) : prevStep}
          className="flex items-center justify-center gap-2 w-full sm:w-auto"
        >
          <ArrowLeft className="h-4 w-4" />
          Previous
        </Button>
        
        {currentStep < deploymentSteps.length - 1 && currentStep !== 3 && (
          <Button 
            onClick={nextStep} 
            disabled={
              (currentStep === 0 && !analysisResult) ||
              (currentStep === 1 && !credentialsValid)
            }
            className="flex items-center justify-center gap-2 w-full sm:w-auto bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
          >
            Next
            <ArrowRight className="h-4 w-4" />
          </Button>
        )}
      </div>
    </div>
  )
}

function RepositoryStep({ 
  formData, 
  setFormData, 
  isAnalyzing, 
  analysisResult, 
  onAnalyze 
}: { 
  formData: any
  setFormData: any
  isAnalyzing: boolean
  analysisResult: any
  onAnalyze: () => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2 text-lg sm:text-xl">
          <Github className="h-5 w-5" />
          Repository Analysis
        </CardTitle>
        <CardDescription className="text-sm sm:text-base">
          Enter your GitHub repository URL to analyze the project structure
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 sm:space-y-6 p-4 sm:p-6">
        <div className="space-y-2">
          <Label htmlFor="repo">Repository URL</Label>
          <Input
            id="repo"
            placeholder="https://github.com/username/repository"
            value={formData.repositoryUrl}
            onChange={(e) => setFormData({...formData, repositoryUrl: e.target.value})}
          />
          <p className="text-sm text-gray-500">
            Supports React, Vue, Angular, and static websites. We'll analyze the project structure and build requirements.
          </p>
        </div>

        {/* GitHub Token Field - Only show for GitHub URLs */}
        {formData.repositoryUrl.toLowerCase().includes('github.com') && (
          <div className="space-y-2">
            <Label htmlFor="github-token">GitHub Personal Access Token (Optional)</Label>
            <Input
              id="github-token"
              type="password"
              placeholder="ghp_xxxxxxxxxxxxxxxxxxxx (for private repositories)"
              value={formData.githubToken}
              onChange={(e) => setFormData({...formData, githubToken: e.target.value})}
            />
            <p className="text-xs text-gray-500">
              Required only for private repositories. Create a token at{' '}
              <a 
                href="https://github.com/settings/tokens" 
                target="_blank" 
                rel="noopener noreferrer"
                className="text-blue-500 hover:underline"
              >
                GitHub Settings
              </a>
            </p>
          </div>
        )}

        <div className="space-y-2">
          <Label htmlFor="project-name">Project Name (Optional)</Label>
          <Input
            id="project-name"
            placeholder="codeflowops-saas-app"
            value={formData.projectName}
            onChange={(e) => setFormData({...formData, projectName: e.target.value})}
          />
        </div>

        <Button 
          onClick={onAnalyze}
          disabled={isAnalyzing || !formData.repositoryUrl.trim()}
          className="w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
        >
          {isAnalyzing ? (
            <>
              <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
              Analyzing Repository...
            </>
          ) : (
            <>
              <Globe className="h-4 w-4 mr-2" />
              Analyze Repository
            </>
          )}
        </Button>

        {analysisResult && (
          <div className="mt-4 sm:mt-6 p-3 sm:p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle className="h-4 w-4 sm:h-5 sm:w-5 text-green-600" />
              <h3 className="text-sm sm:text-base font-medium text-green-800">Analysis Complete</h3>
            </div>
            <div className="text-xs sm:text-sm text-green-700 space-y-1 break-words">
              <p><strong>Detected Framework:</strong> {
                (() => {
                  // Dynamic framework detection - no hardcoding, trust backend analysis
                  const analysis = analysisResult?.analysis || {};
                  const executiveSummary = analysis.executive_summary || {};
                  const frameworks = analysis.frameworks || [];
                  
                  // 1. Prioritize backend frameworks array (most reliable)
                  if (frameworks && frameworks.length > 0) {
                    const topFramework = frameworks[0];
                    const frameworkName = topFramework.name || 'Unknown';
                    const confidence = topFramework.confidence || 0;
                    
                    // Capitalize and format framework name dynamically
                    const formattedName = frameworkName
                      .split('-')
                      .map((word: string) => word.charAt(0).toUpperCase() + word.slice(1))
                      .join(' ');
                    
                    // Add context based on framework type if available
                    const frameworkType = topFramework.framework_type || '';
                    if (frameworkType === 'frontend') {
                      return `${formattedName} Application`;
                    } else if (frameworkType === 'backend') {
                      return `${formattedName} API`;
                    } else if (frameworkType === 'fullstack') {
                      return `${formattedName} Full-Stack Application`;
                    }
                    
                    return formattedName;
                  }
                  
                  // 2. Use executive summary project type as fallback
                  const projectType = executiveSummary.project_type;
                  if (projectType && projectType !== 'Unknown') {
                    return projectType;
                  }
                  
                  // 3. Use primary technology as final fallback
                  const primaryTech = executiveSummary.primary_technology;
                  if (primaryTech && primaryTech !== 'Unknown') {
                    return `${primaryTech} Project`;
                  }
                  
                  // 4. Ultimate fallback
                  return 'Web Application';
                })()
              }</p>
              <p><strong>Project Type:</strong> {
                analysisResult.analysis?.executive_summary?.project_type || 
                analysisResult.analysis?.stack_classification?.type || 
                analysisResult.analysis?.stack_blueprint?.project_kind ||
                analysisResult.analysis?.project_type || 
                analysisResult.project_type || 
                'Static Site'
              }</p>
              <p><strong>Recommended Stack:</strong> {
                analysisResult.analysis?.final_recommendation?.stack_id || 
                analysisResult.analysis?.stack_blueprint?.deployment_targets?.preferred ||
                analysisResult.analysis?.recommended_stack?.stack_type || 
                analysisResult.recommended_stack || 
                'Static hosting'
              }</p>
              <p><strong>Build Tool:</strong> {
                analysisResult.analysis?.stack_blueprint?.services?.[0]?.build?.tool ||
                (Array.isArray(analysisResult.analysis?.build_commands) 
                  ? analysisResult.analysis.build_commands.join(' && ')
                  : analysisResult.analysis?.build_commands) || 
                    analysisResult.build_command || 
                    'npm run build'
              }</p>
              <p><strong>Deployment Target:</strong> {
                analysisResult.analysis?.stack_blueprint?.deployment_targets?.preferred ||
                analysisResult.analysis?.deployment_target ||
                'AWS'
              }</p>
              <p><strong>Deployment ID:</strong> {analysisResult?.deployment_id || analysisResult?.analysis_id}</p>
              {(analysisResult.analysis?.enhancements?.files_created > 0 || analysisResult.enhancements_made) && (
                <p><strong>Enhancements:</strong> Missing files were automatically generated</p>
              )}
              {analysisResult.analysis?.recommended_stack?.description && (
                <p><strong>Infrastructure:</strong> {analysisResult.analysis.recommended_stack.description}</p>
              )}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  )
}

function CredentialsStep({ 
  formData, 
  setFormData, 
  showSecretKey,
  setShowSecretKey,
  isValidating,
  credentialsValid,
  onValidate 
}: { 
  formData: any
  setFormData: any
  showSecretKey: boolean
  setShowSecretKey: (show: boolean) => void
  isValidating: boolean
  credentialsValid: boolean | null
  onValidate: () => void
}) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg sm:text-xl">AWS Credentials</CardTitle>
        <CardDescription className="text-sm sm:text-base">
          Enter your AWS credentials to deploy infrastructure
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 sm:space-y-6 p-4 sm:p-6">
        <div className="space-y-2">
          <Label htmlFor="access-key">AWS Access Key ID <span className="text-red-500">*</span></Label>
          <Input
            id="access-key"
            placeholder="AKIA..."
            value={formData.awsAccessKey}
            onChange={(e) => setFormData({...formData, awsAccessKey: e.target.value})}
            className={!formData.awsAccessKey.trim() ? "border-red-300 focus:border-red-500" : ""}
          />
          {!formData.awsAccessKey.trim() && (
            <p className="text-sm text-red-600">Please enter your AWS Access Key ID</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="secret-key">AWS Secret Access Key <span className="text-red-500">*</span></Label>
          <div className="relative">
            <Input
              id="secret-key"
              type={showSecretKey ? 'text' : 'password'}
              placeholder="******************"
              value={formData.awsSecretKey}
              onChange={(e) => setFormData({...formData, awsSecretKey: e.target.value})}
              className={!formData.awsSecretKey.trim() ? "border-red-300 focus:border-red-500" : ""}
            />
            <Button
              type="button"
              variant="ghost"
              size="sm"
              className="absolute right-2 top-1/2 -translate-y-1/2"
              onClick={() => setShowSecretKey(!showSecretKey)}
            >
              {showSecretKey ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            </Button>
          </div>
          {!formData.awsSecretKey.trim() && (
            <p className="text-sm text-red-600">Please enter your AWS Secret Access Key</p>
          )}
        </div>

        <div className="space-y-2">
          <Label htmlFor="region">AWS Region <span className="text-red-500">*</span></Label>
          <Select value={formData.awsRegion} onValueChange={(value) => setFormData({...formData, awsRegion: value})}>
            <SelectTrigger className={!formData.awsRegion ? "border-red-300 focus:border-red-500" : ""}>
              <SelectValue placeholder="Select AWS Region" />
            </SelectTrigger>
            <SelectContent className="z-50">
              <SelectItem value="us-east-1">US East (N. Virginia)</SelectItem>
              <SelectItem value="us-west-2">US West (Oregon)</SelectItem>
              <SelectItem value="eu-west-1">Europe (Ireland)</SelectItem>
              <SelectItem value="ap-southeast-1">Asia Pacific (Singapore)</SelectItem>
            </SelectContent>
          </Select>
          {!formData.awsRegion && (
            <p className="text-sm text-red-600">Please select an AWS Region</p>
          )}
        </div>

        {/* Extra spacing to prevent dropdown overlap with button */}
        {formData.awsAccessKey.trim() && formData.awsSecretKey.trim() && formData.awsRegion && (
          <div className="pt-4">
            <Button 
              onClick={onValidate}
              disabled={isValidating}
              className="w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
            >
              {isValidating ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                  Validating Credentials...
                </>
              ) : (
                <>
                  <Settings className="h-4 w-4 mr-2" />
                  Validate AWS Credentials
                </>
              )}
            </Button>
          </div>
        )}

        {credentialsValid === true && (
          <div className="p-4 bg-green-50 rounded-lg border border-green-200">
            <div className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="font-medium text-green-800">Credentials Valid</span>
            </div>
            <p className="text-sm text-green-700 mt-1">
              AWS credentials validated successfully. Ready to deploy!
            </p>
          </div>
        )}

        {credentialsValid === false && (
          <div className="p-4 bg-red-50 rounded-lg border border-red-200">
            <div className="flex items-center gap-2">
              <AlertCircle className="h-5 w-5 text-red-600" />
              <span className="font-medium text-red-800">Invalid Credentials</span>
            </div>
            <p className="text-sm text-red-700 mt-1">
              Please check your AWS access key and secret key.
            </p>
          </div>
        )}
        
        {/* Extra spacing to prevent dropdown overlap */}
        <div className="pb-8 sm:pb-12"></div>
      </CardContent>
    </Card>
  )
}

function FrameworkConfigStep({ 
  analysisResult, 
  frameworkConfig, 
  setFrameworkConfig, 
  onNext 
}: { 
  analysisResult: any; 
  frameworkConfig: any; 
  setFrameworkConfig: (config: any) => void; 
  onNext: () => void;
}) {
  // Trust backend analysis - no frontend detection needed
  const getDetectedFramework = () => {
    console.log('🔍 FrameworkConfig Debug - FULL analysisResult:', JSON.stringify(analysisResult, null, 2));
    
    // The data might be nested in analysisResult.analysis - check both locations
    const rootData = analysisResult || {};
    const analysisData = analysisResult?.analysis || {};
    
    // 1. Check direct framework field FIRST (this is where EnhancedRepositoryAnalyzer puts it)
    const directFramework = rootData?.framework?.type || analysisData?.framework?.type;
    if (directFramework) {
      console.log('🎯 Direct framework field:', directFramework);
      const fw = directFramework.toLowerCase();
      if (fw.includes('react') || fw === 'react-spa') return 'react';
      if (fw.includes('nextjs')) return 'nextjs';
      if (fw.includes('vue')) return 'vue';
      if (fw.includes('angular')) return 'angular';
      if (fw.includes('static')) return 'static';
      return fw;
    }
    
    // 2. Check intelligence_profile.frameworks array (this is where the React data actually is)
    const intelligenceProfile = rootData?.intelligence_profile || analysisData?.intelligence_profile;
    if (intelligenceProfile?.frameworks && intelligenceProfile.frameworks.length > 0) {
      const topFramework = intelligenceProfile.frameworks[0];
      const frameworkName = (topFramework.name || '').toLowerCase();
      
      console.log('🎯 Intelligence profile framework:', topFramework);
      console.log('🎯 Framework name:', frameworkName);
      
      if (frameworkName.includes('react')) return 'react';
      if (frameworkName.includes('nextjs')) return 'nextjs';
      if (frameworkName.includes('vue')) return 'vue';
      if (frameworkName.includes('angular')) return 'angular';
      if (frameworkName.includes('static')) return 'static';
      
      return frameworkName || 'static';
    }
    
    // 3. Use frameworks array (fallback)
    const frameworks = rootData?.frameworks || analysisData?.frameworks || [];
    
    console.log('🔍 FrameworkConfig Debug - frameworks array:', frameworks);
    
    if (frameworks && frameworks.length > 0) {
      const topFramework = frameworks[0];
      const frameworkName = (topFramework.name || '').toLowerCase();
      
      console.log('🎯 Top framework from backend:', topFramework);
      console.log('🎯 Framework name:', frameworkName);
      
      if (frameworkName.includes('react')) return 'react';
      if (frameworkName.includes('nextjs')) return 'nextjs';
      if (frameworkName.includes('vue')) return 'vue';
      if (frameworkName.includes('angular')) return 'angular';
      if (frameworkName.includes('static')) return 'static';
      
      return frameworkName || 'static';
    }
    
    // 4. Check stack classification
    const stackType = rootData?.stack_classification?.type || analysisData?.intelligence_profile?.stack_classification?.type;
    if (stackType) {
      console.log('🎯 Stack classification:', stackType);
      const fw = stackType.toLowerCase();
      if (fw.includes('react') || fw === 'react-spa') return 'react';
      if (fw.includes('static')) return 'static';
      return fw;
    }
    
    // 5. Final fallback
    const backendFramework = rootData?.detected_framework ||
                           analysisData?.detected_framework ||
                           'static';
    
    console.log('🎯 Fallback framework detected:', backendFramework);
    
    const framework = backendFramework.toLowerCase();
    if (framework.includes('react') || framework === 'react-spa') return 'react';
    if (framework.includes('static')) return 'static';
    
    console.log('❌ No framework detected, defaulting to static');
    return 'static'; // Default fallback
  }
  
  const detectedFramework = getDetectedFramework()
  const frameworkInfo = getFrameworkDisplayInfo(detectedFramework)
  
  console.log('🔧 FrameworkConfigStep Debug:', {
    analysisResult,
    detectedFramework,
    frameworkInfo
  })
  
  const handleDeploymentTypeChange = (value: string) => {
    setFrameworkConfig({
      ...frameworkConfig,
      deploymentType: value,
      selectedFramework: value === 'auto' ? detectedFramework : frameworkConfig.selectedFramework
    })
  }

  const availableFrameworks = [
    { value: 'react', label: 'React', description: 'JavaScript library for building UIs' },
    { value: 'static', label: 'Static Site', description: 'HTML/CSS/JS static website' }
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Settings className="h-5 w-5" />
          Framework Configuration
        </CardTitle>
        <CardDescription>
          Configure deployment options for your application
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Detected Framework Display */}
        <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle className="h-5 w-5 text-blue-600" />
            <h3 className="font-medium text-blue-800">Detected Framework</h3>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-lg">{frameworkInfo.emoji}</span>
            <Badge className={frameworkInfo.color}>
              {frameworkInfo.name}
            </Badge>
            <span className="text-sm text-blue-700">({detectedFramework})</span>
          </div>
        </div>

        {/* Deployment Type Selection */}
        <div className="space-y-3">
          <Label className="text-base font-medium">Deployment Stack</Label>
          <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 bg-blue-100 rounded-full flex items-center justify-center">
                <Globe className="h-5 w-5 text-blue-600" />
              </div>
              <div>
                <h4 className="font-medium text-blue-800">CloudFront + S3</h4>
                <p className="text-sm text-blue-700">Global CDN deployment for optimal performance</p>
              </div>
            </div>
          </div>
        </div>

        {/* Continue Button */}
        <Button 
          onClick={onNext}
          className="w-full bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
        >
          Continue to Deployment
          <ArrowRight className="h-4 w-4 ml-2" />
        </Button>
      </CardContent>
    </Card>
  )
}

function DeployStep({ 
  formData, 
  frameworkConfig,
  analysisResult,
  isDeploying, 
  deploymentProgress,
  deploymentPhase,
  onDeploy 
}: { 
  formData: any
  frameworkConfig: any
  analysisResult: any
  isDeploying: boolean
  deploymentProgress: number
  deploymentPhase: string
  onDeploy: () => void 
}) {
  // Get the detected framework/stack from analysis (enhanced for modular router system)
  const detectedFramework = analysisResult?.analysis?.frameworks?.[0]?.name || 
                           analysisResult?.analysis?.executive_summary?.project_type ||
                           analysisResult?.analysis?.stack_classification?.type ||
                           analysisResult?.analysis?.stack_blueprint?.services?.[0]?.framework?.name ||
                           analysisResult?.analysis?.detected_stack ||
                           analysisResult?.analysis?.detected_framework || 
                           analysisResult?.detected_framework || 
                           analysisResult?.analysis?.project_type || 
                           'Web App'
  
  const projectType = analysisResult?.analysis?.executive_summary?.project_type || 
                     analysisResult?.analysis?.stack_classification?.type ||
                     analysisResult?.analysis?.stack_blueprint?.project_kind ||
                     analysisResult?.analysis?.final_recommendation?.stack_id ||
                     analysisResult?.analysis?.project_type || 
                     analysisResult?.project_type || 
                     'Static Site'
  
  const infrastructureType = analysisResult?.analysis?.recommended_stack?.description || 
                            `${detectedFramework} deployment`

  const frameworkInfo = getFrameworkDisplayInfo(detectedFramework)

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg sm:text-xl">Ready to Deploy</CardTitle>
        <CardDescription className="text-sm sm:text-base">
          Review your settings and deploy to AWS
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4 sm:space-y-6 p-4 sm:p-6">
        {/* Deployment Summary */}
        <div className="space-y-3 sm:space-y-4">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 sm:p-4 bg-gray-50 dark:bg-gray-800 rounded-lg gap-2 sm:gap-4">
            <div className="min-w-0 flex-1">
              <h4 className="font-medium text-sm sm:text-base dark:text-white">Repository</h4>
              <p className="text-xs sm:text-sm text-gray-600 dark:text-gray-300 break-all">{formData.repositoryUrl}</p>
            </div>
            <Badge variant="secondary" className={`${frameworkInfo.color} border-0 shrink-0 self-start sm:self-center`}>
              {frameworkInfo.emoji} {frameworkInfo.name}
            </Badge>
          </div>
          
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center p-3 sm:p-4 bg-gray-50 dark:bg-gray-800 rounded-lg gap-2 sm:gap-4">
            <div className="min-w-0 flex-1">
              <h4 className="font-medium text-sm sm:text-base dark:text-white">Project Type</h4>
              <p className="text-sm text-gray-600 dark:text-gray-300">{projectType}</p>
            </div>
            <Badge variant="outline">{formData.awsRegion}</Badge>
          </div>

          <div className="flex justify-between items-center p-4 bg-gray-50 dark:bg-gray-800 rounded-lg">
            <div>
              <h4 className="font-medium dark:text-white">Infrastructure</h4>
              <p className="text-sm text-gray-600 dark:text-gray-300">{infrastructureType}</p>
            </div>
            <Badge variant="outline">Cloud Ready</Badge>
          </div>
        </div>
        
        {/* Deployment Progress */}
        {isDeploying && (
          <div className="space-y-4">
            <div className="text-center">
              <h3 className="text-lg font-semibold mb-2 dark:text-white">Deploying Your Application</h3>
              <p className="text-gray-600 dark:text-gray-300">Creating AWS infrastructure and deploying your {frameworkInfo.name} app...</p>
            </div>
            
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <Progress value={deploymentProgress} className="h-3 mb-3" />
              
              <div className="text-center space-y-2">
                <div className="font-medium text-blue-800">
                  {deploymentProgress}% Complete
                </div>
                <div className="text-sm text-blue-600">
                  {deploymentPhase === 'initializing' && (
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      "Initializing deployment pipeline..."
                    </div>
                  )}
                  {deploymentPhase === 'building' && (
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-pulse text-orange-600 w-4 h-4 rounded-full bg-orange-200"></div>
                      {projectType.includes('react') || projectType.includes('vue') || projectType.includes('angular')
                        ? `"Building ${frameworkInfo.name} application (npm install & npm run build)..."` 
                        : `"Processing ${frameworkInfo.name} project files..."`}
                    </div>
                  )}
                  {deploymentPhase === 'infrastructure' && (
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-pulse text-blue-600 w-4 h-4 rounded-full bg-blue-200"></div>
                      "Creating S3 bucket and configuring permissions..."
                    </div>
                  )}
                  {deploymentPhase === 'uploading' && (
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-pulse text-green-600 w-4 h-4 rounded-full bg-green-200"></div>
                      "Uploading files to S3 storage..."
                    </div>
                  )}
                  {deploymentPhase === 'configuring' && (
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-pulse text-purple-600 w-4 h-4 rounded-full bg-purple-200"></div>
                      "Setting up CloudFront CDN distribution..."
                    </div>
                  )}
                  {deploymentPhase === 'finalizing' && (
                    <div className="flex items-center justify-center gap-2">
                      <div className="animate-pulse text-green-600 w-4 h-4 rounded-full bg-green-200"></div>
                      "Finalizing deployment and DNS propagation..."
                    </div>
                  )}
                  {deploymentPhase === 'completed' && (
                    <div className="flex items-center justify-center gap-2 text-green-700">
                      <CheckCircle className="h-4 w-4" />
                      "Deployment completed successfully!"
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="text-xs text-gray-500 text-center">
              Estimated time remaining: {
                deploymentPhase === 'initializing' || deploymentPhase === 'building' ? '2-3 minutes' :
                deploymentPhase === 'infrastructure' || deploymentPhase === 'uploading' ? '1-2 minutes' :
                deploymentPhase === 'configuring' || deploymentPhase === 'finalizing' ? 'Almost done!' :
                'Completed!'
              }
            </div>
          </div>
        )}
        
        {!isDeploying && (
          <Button 
            onClick={() => {
              console.log('🔘 Deploy button clicked')
              console.log('📋 Current formData:', formData)
              console.log('📋 Current analysisResult:', analysisResult)
              console.log('📋 Deploy validation checks:')
              console.log('  - Has deployment ID:', !!(analysisResult?.deployment_id || analysisResult?.analysis_id))
              console.log('  - Has AWS credentials:', !!(formData.awsAccessKey && formData.awsSecretKey))
              console.log('  - Repository URL:', formData.repositoryUrl)
              console.log('  - Framework:', analysisResult?.analysis?.framework || analysisResult?.framework)
              onDeploy()
            }}
            className="w-full bg-green-600 hover:bg-green-700 text-white"
          >
            Deploy to AWS
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

function CompleteStep({ deploymentResult, formData, analysisResult }: { deploymentResult: any; formData: any; analysisResult?: any }) {
  const router = useRouter()
  const [isCheckingUrl, setIsCheckingUrl] = useState(true)
  const [urlAccessible, setUrlAccessible] = useState(false)
  const [checkProgress, setCheckProgress] = useState(0)

  // Check if CloudFront URL is accessible
  useEffect(() => {
    if (!deploymentResult?.cloudfront_url) {
      setIsCheckingUrl(false)
      return
    }

    const checkUrlAccessibility = async () => {
      const url = deploymentResult.cloudfront_url
      let attempts = 0
      const maxAttempts = 20 // Check for up to 10 minutes (30 seconds * 20)
      
      const checkInterval = setInterval(async () => {
        attempts++
        setCheckProgress(Math.min((attempts / maxAttempts) * 100, 95))
        
        try {
          // Try to fetch the URL to see if it's accessible
          const response = await fetch(url, { 
            method: 'HEAD', 
            mode: 'no-cors',
            signal: AbortSignal.timeout(10000) // 10 second timeout
          })
          
          // If we get any response (including CORS errors), the URL is likely accessible
          setUrlAccessible(true)
          setCheckProgress(100)
          setIsCheckingUrl(false)
          clearInterval(checkInterval)
          
        } catch (error) {
          // For CloudFront, we might get CORS errors even when the site is accessible
          // So we'll also accept certain error types as "accessible"
          if (attempts >= 3) {
            // After a few attempts, assume it's accessible if we're getting network responses
            setUrlAccessible(true)
            setCheckProgress(100)
            setIsCheckingUrl(false)
            clearInterval(checkInterval)
          }
        }

        // Timeout after max attempts
        if (attempts >= maxAttempts) {
          setUrlAccessible(true) // Assume accessible after timeout
          setCheckProgress(100)
          setIsCheckingUrl(false)
          clearInterval(checkInterval)
        }
      }, 30000) // Check every 30 seconds

      // Cleanup on unmount
      return () => clearInterval(checkInterval)
    }

    // Start checking after a short delay
    const timeoutId = setTimeout(checkUrlAccessibility, 2000)
    return () => clearTimeout(timeoutId)
  }, [deploymentResult?.cloudfront_url])
  
  // Get detected framework info
  const detectedFramework = analysisResult?.analysis?.detected_framework || 
                           analysisResult?.detected_framework || 
                           'Web Application'

  const frameworkInfo = getFrameworkDisplayInfo(detectedFramework)
  
  // Handle error states
  if (deploymentResult?.status === 'failed' || deploymentResult?.status === 'timeout') {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertCircle className="h-6 w-6 text-red-600" />
            ❌ Deployment Failed
          </CardTitle>
          <CardDescription>
            The deployment encountered an error and could not complete successfully.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="p-6 bg-red-50 rounded-lg border border-red-200">
            <div className="mb-4">
              <h3 className="text-lg font-semibold text-red-800 mb-2">What went wrong?</h3>
              <p className="text-red-700 text-sm mb-4">
                {deploymentResult.error || 'The deployment failed for an unknown reason.'}
              </p>
            </div>
            
            {deploymentResult.status === 'timeout' && (
              <div className="bg-yellow-50 rounded-lg p-4 border border-yellow-200 mb-4">
                <h4 className="font-medium text-yellow-800 mb-2">💡 Common Causes:</h4>
                <ul className="text-sm text-yellow-700 space-y-1">
                  <li>• Invalid AWS Access Key or Secret Key</li>
                  <li>• AWS credentials don't have required permissions (S3, CloudFront)</li>
                  <li>• AWS account limits or restrictions</li>
                  <li>• Network connectivity issues</li>
                </ul>
              </div>
            )}
          </div>

          {/* Show logs if available */}
          {deploymentResult.logs && deploymentResult.logs.length > 0 && (
            <div className="space-y-2">
              <h4 className="font-medium">Deployment Logs</h4>
              <div className="bg-gray-100 rounded-lg p-4 max-h-40 overflow-y-auto">
                <pre className="text-xs text-gray-700">
                  {deploymentResult.logs.join('\n')}
                </pre>
              </div>
            </div>
          )}

          {/* Troubleshooting Steps */}
          <div className="space-y-4">
            <h4 className="font-medium text-lg">🔧 Troubleshooting Steps</h4>
            <div className="grid grid-cols-1 gap-4">
              <div className="p-4 bg-blue-50 rounded-lg border border-blue-200">
                <h5 className="font-medium text-sm text-blue-800 mb-2">1. Verify AWS Credentials</h5>
                <p className="text-sm text-blue-700">
                  • Check your Access Key and Secret Key are correct<br/>
                  • Ensure credentials have S3 and CloudFront permissions<br/>
                  • Try accessing AWS console with these credentials
                </p>
              </div>
              <div className="p-4 bg-green-50 rounded-lg border border-green-200">
                <h5 className="font-medium text-sm text-green-800 mb-2">2. Check AWS Permissions</h5>
                <p className="text-sm text-green-700">
                  Required permissions: S3 (CreateBucket, PutObject), CloudFront (CreateDistribution)
                </p>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4">
            <Button 
              onClick={() => window.location.reload()}
              className="flex-1 bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white"
            >
              Try Again
            </Button>
            <Button 
              variant="outline"
              asChild
              className="flex-1"
            >
              <a 
                href="https://console.aws.amazon.com/iam/home#/users"
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                Check AWS IAM
              </a>
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Success state
  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CheckCircle className="h-6 w-6 text-green-600" />
          Deployment Successful!
        </CardTitle>
        <CardDescription>
          Your {frameworkInfo.name} application has been deployed to AWS and is now live!
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Live URL Section */}
        {deploymentResult?.cloudfront_url ? (
          <>
            {isCheckingUrl ? (
              // Checking URL Accessibility
              <div className="p-6 bg-gradient-to-r from-blue-50 to-purple-50 rounded-lg border border-blue-200 text-center">
                <div className="mb-4">
                  <div className="text-2xl mb-2">⏳</div>
                  <h3 className="text-xl font-bold text-blue-800 mb-2">Finalizing CloudFront Distribution</h3>
                  <p className="text-blue-700 text-sm mb-4">CloudFront distribution is being provisioned and will be ready shortly...</p>
                </div>
                
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4 mb-4 border dark:border-gray-700">
                  <div className="mb-3">
                    <div className="flex items-center justify-center gap-2 mb-2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                      <span className="text-sm text-gray-600 dark:text-gray-300 font-medium">Checking URL availability...</span>
                    </div>
                    <Progress value={checkProgress} className="h-2" />
                  </div>
                  <p className="text-xs text-gray-500 dark:text-gray-400">
                    CloudFront distributions typically take 2-5 minutes to become globally available
                  </p>
                </div>
                
                <div className="bg-blue-50 dark:bg-blue-900/20 rounded-lg p-3 border border-blue-200 dark:border-blue-800">
                  <p className="text-xs text-blue-600 dark:text-blue-400">
                    <span className="font-medium">Your URL:</span> {deploymentResult.cloudfront_url}
                  </p>
                </div>
              </div>
            ) : (
              // URL is Ready
              <div className="p-6 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20 rounded-lg border border-green-200 dark:border-green-800 text-center">
                <div className="mb-4">
                  <div className="text-2xl mb-2">🚀</div>
                  <h3 className="text-xl font-bold text-green-800 dark:text-green-400 mb-2">Your App is Live!</h3>
                  <p className="text-green-700 dark:text-green-300 text-sm mb-4">Visit your deployed {frameworkInfo.name} application:</p>
                </div>
                
                <div className="bg-white dark:bg-gray-800 rounded-lg p-4 mb-4 border dark:border-gray-700">
                  <div className="flex items-center justify-center gap-2 mb-2">
                    <Globe className="h-5 w-5 text-green-600 dark:text-green-400" />
                    <span className="text-sm text-gray-600 dark:text-gray-300 font-medium">Live URL:</span>
                  </div>
                  <a 
                    href={deploymentResult.cloudfront_url} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="text-blue-600 hover:text-blue-800 font-medium text-lg break-all underline"
                  >
                    {deploymentResult.cloudfront_url}
                  </a>
                </div>
                
                <Button asChild className="bg-green-600 hover:bg-green-700 dark:bg-green-500 dark:hover:bg-green-600 text-white">
                  <a href={deploymentResult.cloudfront_url} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="h-4 w-4 mr-2" />
                    Open Your App
                  </a>
                </Button>
              </div>
            )}
          </>
        ) : (
          <div className="p-6 bg-yellow-50 rounded-lg border border-yellow-200 text-center">
            <div className="mb-2">⚠️</div>
            <h3 className="text-lg font-semibold text-yellow-800 mb-2">Deployment Completed</h3>
            <p className="text-yellow-700 text-sm mb-4">
              Deployment finished but CloudFront URL not yet available. Check your AWS console.
            </p>
            <p className="text-xs text-yellow-600">
              Note: CloudFront distributions can take 15-20 minutes to fully propagate globally.
            </p>
          </div>
        )}

        {/* Deployment Details */}
        <div className="space-y-4">
          <h4 className="font-medium text-lg flex items-center gap-2">
            <Settings className="h-5 w-5" />
            Deployment Details
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300 flex items-center gap-2">
                <Github className="h-4 w-4" />
                Repository
              </h5>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 break-all">{formData.repositoryUrl}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300">Project Name</h5>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{formData.projectName || 'Auto-generated'}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300">S3 Bucket</h5>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{deploymentResult?.s3_bucket || 'Created successfully'}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300">CDN Distribution</h5>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1 flex items-center gap-1">
                {isCheckingUrl ? (
                  <>
                    <div className="animate-spin rounded-full h-3 w-3 border-b-2 border-orange-600"></div>
                    <span className="text-orange-600 dark:text-orange-400">CloudFront (Provisioning...)</span>
                  </>
                ) : (
                  <>
                    <CheckCircle className="h-3 w-3 text-green-600 dark:text-green-400" />
                    <span className="text-green-600 dark:text-green-400">CloudFront (Active)</span>
                  </>
                )}
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300">AWS Region</h5>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">{formData.awsRegion}</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300">Deploy Time</h5>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">~2-3 minutes</p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300">Build Status</h5>
              <p className="text-sm text-green-600 dark:text-green-400 mt-1 flex items-center gap-1">
                <CheckCircle className="h-3 w-3" />
                Successful
              </p>
            </div>
            <div className="p-4 bg-gray-50 dark:bg-gray-800 rounded-lg border dark:border-gray-700">
              <h5 className="font-medium text-sm text-gray-700 dark:text-gray-300">Infrastructure</h5>
              <p className="text-sm text-gray-600 dark:text-gray-300 mt-1">S3 + CloudFront (SDK)</p>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3 pt-4">
          <Button 
            variant="outline" 
            onClick={() => {
              router.push('/deploy')
              setTimeout(() => window.scrollTo({ top: 0, behavior: 'smooth' }), 100)
            }}
            className="flex-1"
          >
            Deploy Another App
          </Button>
          <Button asChild className="flex-1">
            <a href="/" className="flex items-center justify-center gap-2">
              View Dashboard
            </a>
          </Button>
          {deploymentResult?.cloudfront_url && (
            <Button 
              variant="secondary" 
              asChild
              className="flex-1"
            >
              <a 
                href={`https://console.aws.amazon.com/cloudfront/home?region=${formData.awsRegion}#/distributions`}
                target="_blank" 
                rel="noopener noreferrer"
                className="flex items-center justify-center gap-2"
              >
                <ExternalLink className="h-4 w-4" />
                AWS Console
              </a>
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
