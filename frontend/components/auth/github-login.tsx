'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Github, Loader2, ExternalLink } from 'lucide-react'

interface GitHubLoginProps {
  onSuccess?: () => void
  className?: string
}

export function GitHubLogin({ onSuccess, className }: GitHubLoginProps) {
  const [loading, setLoading] = useState(false)

  const handleGitHubLogin = () => {
    setLoading(true)
    
    // Redirect to GitHub OAuth - using direct EB URL to bypass routing issues
    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://codeflowops.us-east-1.elasticbeanstalk.com'
    window.location.href = `${API_BASE}/api/v1/auth/github`
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Github className="h-5 w-5" />
          Sign in with GitHub
        </CardTitle>
        <CardDescription>
          Connect your GitHub account to access CodeFlowOps features
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Button 
          onClick={handleGitHubLogin}
          disabled={loading}
          className="w-full"
          size="lg"
        >
          {loading ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Redirecting to GitHub...
            </>
          ) : (
            <>
              <Github className="mr-2 h-4 w-4" />
              Continue with GitHub
              <ExternalLink className="ml-2 h-3 w-3" />
            </>
          )}
        </Button>
        
        <div className="mt-4 text-xs text-muted-foreground text-center">
          By signing in, you agree to our Terms of Service and Privacy Policy.
          <br />
          We'll only access your public repositories and profile information.
        </div>
      </CardContent>
    </Card>
  )
}
