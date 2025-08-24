'use client'
import { useEffect, useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
// Using simple emoji icons instead of heroicons for compatibility

interface DeploymentResult {
  success: boolean
  deploymentId: string
  repositoryUrl: string
  repositoryName: string
  liveUrl: string
  s3Bucket: string
  cloudfrontId: string
  cloudfrontDomain: string
  filesUploaded: number
  deploymentTime: string
  framework: string
  language: string
  error?: string
}

function DeploymentSuccessPageContent() {
  const searchParams = useSearchParams()
  const [deploymentResult, setDeploymentResult] = useState<DeploymentResult | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const deploymentId = searchParams.get('deploymentId')
    const success = searchParams.get('success') === 'true'
    
    if (deploymentId) {
      // Fetch deployment results from backend
      fetchDeploymentResult(deploymentId)
    } else {
      // Fallback data from URL params
      const fallbackResult: DeploymentResult = {
        success: success,
        deploymentId: deploymentId || 'unknown',
        repositoryUrl: searchParams.get('repo') || '',
        repositoryName: searchParams.get('repoName') || 'Unknown Repository',
        liveUrl: searchParams.get('liveUrl') || '',
        s3Bucket: searchParams.get('s3Bucket') || '',
        cloudfrontId: searchParams.get('cloudfrontId') || '',
        cloudfrontDomain: searchParams.get('cloudfrontDomain') || '',
        filesUploaded: parseInt(searchParams.get('filesUploaded') || '0'),
        deploymentTime: searchParams.get('deploymentTime') || new Date().toISOString(),
        framework: searchParams.get('framework') || 'static',
        language: searchParams.get('language') || 'HTML',
        error: searchParams.get('error') || undefined
      }
      setDeploymentResult(fallbackResult)
      setLoading(false)
    }
  }, [searchParams])

  const fetchDeploymentResult = async (deploymentId: string) => {
    try {
      const response = await fetch(`http://localhost:8000/api/deployment/${deploymentId}/result`)
      if (response.ok) {
        const result = await response.json()
        setDeploymentResult(result)
      } else {
        console.error('Failed to fetch deployment result')
      }
    } catch (error) {
      console.error('Error fetching deployment result:', error)
    } finally {
      setLoading(false)
    }
  }

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text)
    // You could add a toast notification here
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p className="mt-4 text-gray-600">Loading deployment results...</p>
        </div>
      </div>
    )
  }

  if (!deploymentResult) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-orange-100 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-red-600 mb-4">No Deployment Results Found</h1>
          <Link href="/deploy" className="text-blue-600 hover:underline">
            Start New Deployment
          </Link>
        </div>
      </div>
    )
  }

  const { success, error } = deploymentResult

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-indigo-50">
      <div className="container mx-auto px-4 py-8">
        <div className="max-w-4xl mx-auto">
          {/* Header */}
          <div className="text-center mb-8">
            {success ? (
              <div className="flex items-center justify-center mb-4">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center">
                  <span className="text-green-600 text-3xl">✓</span>
                </div>
              </div>
            ) : (
              <div className="flex items-center justify-center mb-4">
                <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center">
                  <span className="text-red-600 text-2xl font-bold">✗</span>
                </div>
              </div>
            )}
            
            <h1 className="text-4xl font-bold text-gray-900 mb-2">
              {success ? 'Deployment Successful!' : 'Deployment Failed'}
            </h1>
            
            <p className="text-xl text-gray-600 mb-4">
              {success 
                ? 'Your website has been successfully deployed to AWS' 
                : 'There was an issue during deployment'}
            </p>

            <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
              <h2 className="text-lg font-semibold text-gray-800 mb-2">Repository</h2>
              <p className="text-gray-600">{deploymentResult.repositoryName}</p>
              {deploymentResult.repositoryUrl && (
                <a 
                  href={deploymentResult.repositoryUrl} 
                  target="_blank" 
                  rel="noopener noreferrer"
                  className="text-blue-600 hover:underline inline-flex items-center mt-1"
                >
                  View Source <span className="ml-1">🔗</span>
                </a>
              )}
            </div>
          </div>

          {success ? (
            <div className="space-y-6">
              {/* Live Website */}
              <div className="bg-white rounded-lg shadow-lg border-0 hover:shadow-xl transition-shadow p-6">
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 bg-green-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-green-600 text-xl">🌐</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800">Live Website</h3>
                </div>
                
                <div className="bg-gray-50 rounded-lg p-4 mb-4">
                  <p className="text-sm text-gray-600 mb-2">Your website is live at:</p>
                  <div className="flex items-center justify-between">
                    <a 
                      href={`https://${deploymentResult.cloudfrontDomain}`}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="text-blue-600 hover:underline text-lg font-mono break-all"
                    >
                      https://{deploymentResult.cloudfrontDomain}
                    </a>
                    <button 
                      onClick={() => copyToClipboard(`https://${deploymentResult.cloudfrontDomain}`)}
                      className="ml-2 px-3 py-1 bg-blue-100 text-blue-700 rounded text-sm hover:bg-blue-200 transition-colors"
                    >
                      Copy
                    </button>
                  </div>
                </div>

                {/* CloudFront deployment warning */}
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
                  <div className="flex items-center">
                    <div className="w-8 h-8 bg-yellow-100 rounded-full flex items-center justify-center mr-3">
                      <span className="text-yellow-600">⚠️</span>
                    </div>
                    <div>
                      <p className="text-yellow-800 font-medium">CloudFront Deployment in Progress</p>
                      <p className="text-yellow-700 text-sm mt-1">
                        Your website is deploying globally. It may take 5-15 minutes for the CloudFront URL to be fully accessible worldwide.
                        You can check the status in your AWS CloudFront console.
                      </p>
                    </div>
                  </div>
                </div>

                <button 
                  onClick={() => window.open(`https://${deploymentResult.cloudfrontDomain}`, '_blank')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-3 rounded-lg transition-colors inline-flex items-center"
                >
                  <span className="mr-2">🔗</span>
                  Visit Your Website
                </button>
              </div>

              {/* AWS Resources */}
              <div className="bg-white rounded-lg shadow-lg border-0 hover:shadow-xl transition-shadow p-6">
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-blue-600 text-xl">☁️</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800">AWS Resources Created</h3>
                </div>
                
                <div className="grid md:grid-cols-2 gap-4">
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-700 mb-2">S3 Bucket</h4>
                    <p className="text-gray-600 font-mono text-sm break-all">{deploymentResult.s3Bucket}</p>
                    <p className="text-xs text-gray-500 mt-1">Static file hosting</p>
                  </div>
                  
                  <div className="bg-gray-50 rounded-lg p-4">
                    <h4 className="font-semibold text-gray-700 mb-2">CloudFront Distribution</h4>
                    <p className="text-gray-600 font-mono text-sm">{deploymentResult.cloudfrontId}</p>
                    <p className="text-xs text-gray-500 mt-1">Global CDN & HTTPS</p>
                  </div>
                </div>
              </div>

              {/* Deployment Summary */}
              <div className="bg-white rounded-lg shadow-lg border-0 hover:shadow-xl transition-shadow p-6">
                <div className="flex items-center mb-4">
                  <div className="w-12 h-12 bg-purple-100 rounded-full flex items-center justify-center mr-3">
                    <span className="text-purple-600 text-xl">📊</span>
                  </div>
                  <h3 className="text-xl font-semibold text-gray-800">Deployment Summary</h3>
                </div>
                
                <div className="grid md:grid-cols-3 gap-4">
                  <div className="text-center bg-gray-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-green-600">{deploymentResult.filesUploaded}</div>
                    <div className="text-sm text-gray-600">Files Uploaded</div>
                  </div>
                  
                  <div className="text-center bg-gray-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-blue-600">{deploymentResult.framework}</div>
                    <div className="text-sm text-gray-600">Framework</div>
                  </div>
                  
                  <div className="text-center bg-gray-50 rounded-lg p-4">
                    <div className="text-2xl font-bold text-purple-600">{deploymentResult.language}</div>
                    <div className="text-sm text-gray-600">Primary Language</div>
                  </div>
                </div>

                <div className="flex items-center justify-center mt-4 text-gray-500">
                  <span className="mr-1">🕒</span>
                  <span className="text-sm">
                    Deployed {new Date(deploymentResult.deploymentTime).toLocaleString()}
                  </span>
                </div>
              </div>

              {/* Next Steps */}
              <div className="bg-white rounded-lg shadow-lg border-0 hover:shadow-xl transition-shadow p-6">
                <h3 className="text-xl font-semibold text-gray-800 mb-4">Next Steps</h3>
                <ul className="space-y-2 text-gray-600">
                  <li>• <strong>Custom Domain:</strong> Configure Route 53 for your own domain</li>
                  <li>• <strong>SSL Certificate:</strong> HTTPS is automatically enabled via CloudFront</li>
                  <li>• <strong>Updates:</strong> Redeploy anytime to update your website</li>
                  <li>• <strong>Monitoring:</strong> View CloudWatch metrics in AWS Console</li>
                </ul>
              </div>
            </div>
          ) : (
            /* Error Display */
            <div className="bg-white rounded-lg shadow-lg border-0 hover:shadow-xl transition-shadow p-6">
              <div className="flex items-center mb-4">
                <div className="w-12 h-12 bg-red-100 rounded-full flex items-center justify-center mr-3">
                  <span className="text-red-600 text-xl">❌</span>
                </div>
                <h3 className="text-xl font-semibold text-gray-800">Deployment Error</h3>
              </div>
              
              <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
                <p className="text-red-700">{error || 'An unknown error occurred during deployment.'}</p>
              </div>
              
              <div className="flex space-x-4">
                <Link 
                  href="/deploy"
                  className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
                >
                  Try Again
                </Link>
                <button className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                  Contact Support
                </button>
              </div>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex justify-center space-x-4 mt-8">
            <Link 
              href="/deploy"
              className="px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
            >
              Deploy Another Project
            </Link>
            <Link 
              href="/"
              className="px-6 py-3 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
            >
              Back to Home
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function DeploymentSuccessPage() {
  return (
    <Suspense fallback={<div className="flex justify-center items-center min-h-screen">Loading...</div>}>
      <DeploymentSuccessPageContent />
    </Suspense>
  )
}
