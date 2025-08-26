/**
 * Updated Repository Analysis Component
 * Demonstrates integration with the new modular router system
 */

'use client'

import React, { useState } from 'react'
import { useAnalyzeRepository, useSmartDeployment, useApiHealth, useAvailableStacks, STACK_TYPES } from '@/hooks/use-api-modular'

interface Credentials {
  aws_access_key: string
  aws_secret_key: string
  aws_region: string
}

export default function ModularRepositoryAnalysis() {
  const [repoUrl, setRepoUrl] = useState('')
  const [githubToken, setGithubToken] = useState('')
  const [credentials, setCredentials] = useState<Credentials>({
    aws_access_key: '',
    aws_secret_key: '',
    aws_region: 'us-east-1'
  })
  const [analysis, setAnalysis] = useState<any>(null)
  const [projectName, setProjectName] = useState('')

  // API hooks
  const analyzeRepo = useAnalyzeRepository()
  const smartDeploy = useSmartDeployment()
  const apiHealth = useApiHealth()
  const availableStacks = useAvailableStacks()

  // Check if URL is a GitHub URL
  const isGitHubUrl = repoUrl.toLowerCase().includes('github.com')

  const handleAnalyze = async () => {
    if (!repoUrl) return
    
    try {
      const result = await analyzeRepo.mutateAsync({
        repositoryUrl: repoUrl,
        githubToken: githubToken || undefined
      })
      setAnalysis(result)
      
      // Auto-generate project name if not provided
      if (!projectName) {
        const repoName = repoUrl.split('/').pop()?.replace('.git', '') || 'my-project'
        setProjectName(repoName)
      }
    } catch (error) {
      console.error('Analysis failed:', error)
    }
  }

  const handleDeploy = async () => {
    if (!analysis || !projectName || !credentials.aws_access_key) return

    try {
      const result = await smartDeploy.mutateAsync({
        analysis,
        credentials,
        project_name: projectName,
        repo_url: repoUrl
      })
      
      console.log('Deployment started:', result)
    } catch (error) {
      console.error('Deployment failed:', error)
    }
  }

  const getStackIcon = (stackType: string) => {
    const icons = {
      [STACK_TYPES.REACT]: '⚛️',
      [STACK_TYPES.NEXTJS]: '▲',
      [STACK_TYPES.STATIC]: '🌐',
      [STACK_TYPES.PYTHON]: '🐍',
      [STACK_TYPES.PHP]: '🐘',
      [STACK_TYPES.ANGULAR]: '🅰️'
    }
    return icons[stackType as keyof typeof icons] || '📦'
  }

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      {/* API Health Status */}
      <div className="bg-gray-100 p-4 rounded-lg">
        <h3 className="font-semibold mb-2">🔌 API Status</h3>
        {apiHealth.data ? (
          <div className="flex items-center space-x-4">
            <span className={`px-2 py-1 rounded text-sm ${
              apiHealth.data.using === 'modular' ? 'bg-green-100 text-green-800' :
              apiHealth.data.using === 'legacy' ? 'bg-yellow-100 text-yellow-800' :
              'bg-red-100 text-red-800'
            }`}>
              {apiHealth.data.using === 'modular' && '✅ Modular API'}
              {apiHealth.data.using === 'legacy' && '⚠️ Legacy API'}
              {apiHealth.data.using === 'none' && '❌ No API Available'}
            </span>
            
            {availableStacks.data && (
              <span className="text-sm text-gray-600">
                {availableStacks.data.available_stacks?.length || 0} stack routers loaded
              </span>
            )}
          </div>
        ) : (
          <div className="animate-pulse text-gray-500">Checking API status...</div>
        )}
      </div>

      {/* Repository Analysis */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold">📊 Repository Analysis</h2>
        
        <div className="space-y-2">
          <label className="block text-sm font-medium">GitHub Repository URL</label>
          <input
            type="url"
            value={repoUrl}
            onChange={(e) => setRepoUrl(e.target.value)}
            placeholder="https://github.com/username/repo-name"
            className="w-full p-2 border border-gray-300 rounded"
          />
          
          {/* GitHub Token Field - Only show for GitHub URLs */}
          {isGitHubUrl && (
            <div className="mt-3">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                GitHub Personal Access Token (Optional)
              </label>
              <input
                type="password"
                value={githubToken}
                onChange={(e) => setGithubToken(e.target.value)}
                placeholder="ghp_xxxxxxxxxxxxxxxxxxxx (for private repositories)"
                className="w-full p-2 border border-gray-300 rounded"
              />
              <p className="text-xs text-gray-500 mt-1">
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
          
          <button
            onClick={handleAnalyze}
            disabled={!repoUrl || analyzeRepo.isPending}
            className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 disabled:opacity-50"
          >
            {analyzeRepo.isPending ? 'Analyzing...' : 'Analyze Repository'}
          </button>
        </div>

        {analyzeRepo.error && (
          <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
            Analysis failed: {analyzeRepo.error.message}
          </div>
        )}
      </div>

      {/* Analysis Results */}
      {analysis && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">🎯 Analysis Results</h3>
          
          <div className="grid md:grid-cols-2 gap-4">
            {/* Stack Detection */}
            <div className="space-y-2">
              <h4 className="font-medium text-gray-700">Detected Stack</h4>
              <div className="flex items-center space-x-2">
                <span className="text-2xl">{getStackIcon(analysis.stack_detected)}</span>
                <span className="font-mono bg-gray-100 px-2 py-1 rounded">
                  {analysis.stack_detected || analysis.detected_stack || 'unknown'}
                </span>
              </div>
              
              {analysis.deployment_url && (
                <p className="text-sm text-green-600">
                  ✅ Stack-specific router available
                </p>
              )}
            </div>

            {/* Project Info */}
            <div className="space-y-2">
              <h4 className="font-medium text-gray-700">Project Details</h4>
              <div className="text-sm space-y-1">
                <p><span className="font-medium">Type:</span> {analysis.project_type || 'Unknown'}</p>
                <p><span className="font-medium">Confidence:</span> {Math.round((analysis.confidence || 0) * 100)}%</p>
                {analysis.framework && (
                  <p><span className="font-medium">Framework:</span> {analysis.framework}</p>
                )}
              </div>
            </div>
          </div>

          {/* Infrastructure Preview */}
          {analysis.infrastructure && (
            <div className="mt-4 p-3 bg-blue-50 rounded">
              <h4 className="font-medium text-blue-800 mb-2">🏗️ Recommended Infrastructure</h4>
              <div className="text-sm text-blue-700">
                <p><span className="font-medium">Type:</span> {analysis.infrastructure.type}</p>
                {analysis.infrastructure.services && (
                  <p><span className="font-medium">Services:</span> {analysis.infrastructure.services.join(', ')}</p>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Deployment Configuration */}
      {analysis && (
        <div className="bg-white border border-gray-200 rounded-lg p-6">
          <h3 className="text-lg font-semibold mb-4">🚀 Deployment Configuration</h3>
          
          <div className="space-y-4">
            {/* Project Name */}
            <div>
              <label className="block text-sm font-medium mb-1">Project Name</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                placeholder="my-awesome-project"
                className="w-full p-2 border border-gray-300 rounded"
              />
            </div>

            {/* AWS Credentials */}
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <label className="block text-sm font-medium mb-1">AWS Access Key</label>
                <input
                  type="text"
                  value={credentials.aws_access_key}
                  onChange={(e) => setCredentials(prev => ({ ...prev, aws_access_key: e.target.value }))}
                  placeholder="AKIA..."
                  className="w-full p-2 border border-gray-300 rounded"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">AWS Secret Key</label>
                <input
                  type="password"
                  value={credentials.aws_secret_key}
                  onChange={(e) => setCredentials(prev => ({ ...prev, aws_secret_key: e.target.value }))}
                  placeholder="••••••••"
                  className="w-full p-2 border border-gray-300 rounded"
                />
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-1">AWS Region</label>
                <select
                  value={credentials.aws_region}
                  onChange={(e) => setCredentials(prev => ({ ...prev, aws_region: e.target.value }))}
                  className="w-full p-2 border border-gray-300 rounded"
                >
                  <option value="us-east-1">us-east-1</option>
                  <option value="us-west-2">us-west-2</option>
                  <option value="eu-west-1">eu-west-1</option>
                </select>
              </div>
            </div>

            {/* Deploy Button */}
            <button
              onClick={handleDeploy}
              disabled={!projectName || !credentials.aws_access_key || smartDeploy.isPending}
              className="w-full px-4 py-3 bg-green-500 text-white rounded hover:bg-green-600 disabled:opacity-50 font-medium"
            >
              {smartDeploy.isPending ? 'Deploying...' : `🚀 Deploy ${analysis.stack_detected} Application`}
            </button>

            {smartDeploy.error && (
              <div className="p-3 bg-red-100 border border-red-300 rounded text-red-700">
                Deployment failed: {smartDeploy.error.message}
              </div>
            )}

            {smartDeploy.data && (
              <div className="p-3 bg-green-100 border border-green-300 rounded text-green-700">
                ✅ Deployment started successfully! 
                {smartDeploy.data.deployment_id && (
                  <span className="font-mono ml-2">{smartDeploy.data.deployment_id}</span>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* Available Stacks Debug Info */}
      {availableStacks.data && (
        <details className="bg-gray-50 p-4 rounded">
          <summary className="font-medium cursor-pointer">🔧 Available Stack Routers</summary>
          <div className="mt-2 text-sm">
            <pre className="bg-gray-100 p-2 rounded overflow-auto">
              {JSON.stringify(availableStacks.data, null, 2)}
            </pre>
          </div>
        </details>
      )}
    </div>
  )
}
