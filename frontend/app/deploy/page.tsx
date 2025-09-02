'use client'

import { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { SDKDeploymentWizard } from '@/components/deployment/sdk-deployment-wizard'
import { Rocket, Github, Zap, ArrowRight } from 'lucide-react'
import { useAuthGuard } from '@/hooks/use-auth-guard'
import { Skeleton } from '@/components/ui/skeleton'

function DeployPageContent() {
  const [showDeploymentFlow, setShowDeploymentFlow] = useState(false)
  const [prefilledRepo, setPrefilledRepo] = useState('')
  const [oauthProcessing, setOauthProcessing] = useState(false)
  const searchParams = useSearchParams()

  // Check for OAuth callback parameters first
  useEffect(() => {
    const handleOAuthCallback = async () => {
      const success = searchParams.get('success')
      const accessToken = searchParams.get('access_token')
      const userEmail = searchParams.get('email')
      const userId = searchParams.get('user_id')

      if (success === 'true' && accessToken && userEmail) {
        setOauthProcessing(true)
        
        try {
          // Store OAuth tokens in localStorage for the auth system
          localStorage.setItem('auth_token', accessToken)
          localStorage.setItem('user_email', userEmail)
          localStorage.setItem('user_id', userId || '')
          
          // Clear OAuth params from URL
          const newUrl = window.location.pathname
          window.history.replaceState({}, '', newUrl)
          
          // Auto-start deployment flow for authenticated OAuth users
          setShowDeploymentFlow(true)
        } catch (error) {
          console.error('OAuth callback processing error:', error)
        } finally {
          setOauthProcessing(false)
        }
      }
    }

    handleOAuthCallback()
  }, [searchParams])

  // Use auth guard only if not processing OAuth
  const { isAuthenticated, loading } = useAuthGuard(oauthProcessing ? null : '/login')

  useEffect(() => {
    // Only proceed if authenticated and not processing OAuth
    if (!loading && !oauthProcessing && isAuthenticated) {
      // Check if there's a repo parameter in the URL
      const repo = searchParams.get('repo')
      if (repo) {
        setPrefilledRepo(decodeURIComponent(repo))
        // Automatically start the deployment flow if there's a repo URL
        setShowDeploymentFlow(true)
      }
    }
  }, [searchParams, loading, isAuthenticated, oauthProcessing])

  // Show loading skeleton while checking authentication or processing OAuth
  if (loading || oauthProcessing) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-950 dark:to-blue-950">
        <div className="container mx-auto px-4 py-16">
          <div className="text-center mb-16">
            <Skeleton className="w-48 h-8 mx-auto mb-6" />
            <Skeleton className="w-96 h-12 mx-auto mb-6" />
            <Skeleton className="w-[600px] h-20 mx-auto" />
          </div>
        </div>
      </div>
    )
  }

  // Don't render content if not authenticated and not processing OAuth (guard will redirect)
  if (!isAuthenticated && !oauthProcessing) {
    return null
  }



  if (showDeploymentFlow) {
    return <SDKDeploymentWizard 
      initialRepo={prefilledRepo} 
      onClose={() => setShowDeploymentFlow(false)}
    />
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50 dark:from-gray-900 dark:via-gray-950 dark:to-blue-950">
      <div className="container mx-auto px-4 py-16">
        {/* Header */}
        <div className="text-center mb-16">
          <div className="inline-flex items-center gap-2 bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-300 px-4 py-2 rounded-full text-sm font-medium mb-6">
            <Rocket className="w-4 h-4" />
            Deploy to AWS in Minutes
          </div>
          <h1 className="text-5xl font-bold text-gray-900 dark:text-white mb-6">
            From GitHub to
            <span className="bg-gradient-to-r from-blue-600 to-indigo-600 bg-clip-text text-transparent"> Production</span>
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto mb-8">
            Transform your GitHub repository into a production-ready AWS deployment with intelligent 
            infrastructure provisioning, automated CI/CD, and enterprise-grade security.
          </p>
          <Button 
            size="lg" 
            className="bg-blue-600 hover:bg-blue-700 text-white px-8 py-4 text-lg"
            onClick={() => setShowDeploymentFlow(true)}
          >
            <Github className="w-5 h-5 mr-2" />
            Deploy Your Repository
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 mb-16">
          <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow dark:bg-gray-800 dark:border-gray-700">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Github className="w-8 h-8 text-blue-600 dark:text-blue-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 dark:text-white">Smart Analysis</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Automatically detects your tech stack and recommends the optimal AWS infrastructure pattern.
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow dark:bg-gray-800 dark:border-gray-700">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-green-100 dark:bg-green-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Zap className="w-8 h-8 text-green-600 dark:text-green-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 dark:text-white">Instant Infrastructure</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Provisions optimal AWS infrastructure: S3 + CloudFront for static sites, Lambda for serverless apps, or ECS for containers.
              </p>
            </CardContent>
          </Card>

          <Card className="border-0 shadow-lg hover:shadow-xl transition-shadow dark:bg-gray-800 dark:border-gray-700">
            <CardContent className="p-8 text-center">
              <div className="w-16 h-16 bg-purple-100 dark:bg-purple-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <Rocket className="w-8 h-8 text-purple-600 dark:text-purple-400" />
              </div>
              <h3 className="text-xl font-semibold mb-3 dark:text-white">Live in Minutes</h3>
              <p className="text-gray-600 dark:text-gray-300">
                Complete deployment pipeline from repository analysis to live application in under 15 minutes.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Process Steps */}
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-xl dark:shadow-gray-900/50 p-12">
          <div className="text-center mb-12">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">How It Works</h2>
            <p className="text-lg text-gray-600 dark:text-gray-300">
              Our intelligent deployment process handles everything automatically
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            {[
              {
                step: '1',
                title: 'Repository Analysis',
                description: 'Analyze your GitHub repository to detect framework, dependencies, and infrastructure needs.'
              },
              {
                step: '2',
                title: 'Infrastructure Planning',
                description: 'Generate optimal AWS infrastructure configuration with cost estimates.'
              },
              {
                step: '3',
                title: 'Secure Deployment',
                description: 'Provision AWS resources using your encrypted credentials with full audit logging.'
              },
              {
                step: '4',
                title: 'Live Application',
                description: 'Your application goes live with monitoring, scaling, and CI/CD pipeline ready.'
              }
            ].map((step, index) => (
              <div key={index} className="text-center">
                <div className="w-12 h-12 bg-blue-600 dark:bg-blue-500 text-white rounded-full flex items-center justify-center mx-auto mb-4 text-lg font-bold">
                  {step.step}
                </div>
                <h3 className="font-semibold mb-2 text-gray-900 dark:text-white">{step.title}</h3>
                <p className="text-gray-600 dark:text-gray-300 text-sm">{step.description}</p>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-16">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
            Ready to Deploy?
          </h2>
          <p className="text-lg text-gray-600 dark:text-gray-300 mb-8">
            Join thousands of developers who trust our platform for their production deployments
          </p>
          <Button 
            size="lg" 
            className="bg-blue-600 hover:bg-blue-700 dark:bg-blue-500 dark:hover:bg-blue-600 text-white px-8 py-4 text-lg"
            onClick={() => setShowDeploymentFlow(true)}
          >
            Start Your Deployment
            <ArrowRight className="w-5 h-5 ml-2" />
          </Button>
        </div>
      </div>
    </div>
  )
}

export default function DeployPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <DeployPageContent />
    </Suspense>
  )
}
