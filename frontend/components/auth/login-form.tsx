'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Mail, Lock, Eye, EyeOff, AlertCircle } from 'lucide-react'

interface LoginFormProps {
  redirectTo?: string
}

export function LoginForm({ redirectTo = '/deploy' }: LoginFormProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')

  const { login, isAuthenticated, loading } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  // Check for OAuth success and redirect
  useEffect(() => {
    const authenticated = searchParams.get('authenticated')
    if (authenticated === 'true' && !loading) {
      // Give the auth context a moment to update, then redirect
      setTimeout(() => {
        if (isAuthenticated) {
          router.push(redirectTo)
        } else {
          // If still not authenticated after OAuth success, force a page reload
          // to trigger fresh auth check
          window.location.reload()
        }
      }, 1000)
    }
  }, [searchParams, isAuthenticated, loading, router, redirectTo])

  // Auto-redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated && !loading) {
      router.push(redirectTo)
    }
  }, [isAuthenticated, loading, router, redirectTo])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Basic validation
    if (!username.trim() || !password.trim()) {
      setError('Please fill in all fields')
      setIsLoading(false)
      return
    }

    try {
      await login({ username: username.trim(), password })
      router.push(redirectTo)
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Login failed. Please try again.'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Sign in to CodeFlowOps</CardTitle>
          <CardDescription className="text-center">
            Enter your credentials to access your account
          </CardDescription>
        </CardHeader>

        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertCircle className="h-4 w-4" />
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

              <div className="space-y-2">
                <Label htmlFor="username">Username or Email</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="username"
                    type="text"
                    placeholder="Enter your username or email"
                    value={username}
                    onChange={(e) => setUsername(e.target.value)}
                    required
                    className="pl-10"
                    disabled={isLoading}
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="password">Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="password"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    className="pl-10 pr-10"
                    disabled={isLoading}
                  />
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                    onClick={() => setShowPassword(!showPassword)}
                    disabled={isLoading}
                  >
                    {showPassword ? (
                      <EyeOff className="h-4 w-4 text-gray-400" />
                    ) : (
                      <Eye className="h-4 w-4 text-gray-400" />
                    )}
                  </Button>
                </div>
              </div>

              <Button
                type="submit"
                className="w-full"
                disabled={isLoading}
              >
                {isLoading ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Signing in...
                  </>
                ) : (
                  'Sign in'
                )}
              </Button>

              {/* GitHub Login Section */}
              <div className="relative">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-background px-2 text-muted-foreground">
                    Or continue with
                  </span>
                </div>
              </div>

              <Button
                type="button"
                variant="outline"
                className="w-full"
                onClick={async () => {
                  try {
                    const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
                    const redirectUri = `${window.location.origin}/auth/callback?next=/profile`
                    
                    // Get GitHub authorization URL from backend
                    const response = await fetch(
                      `${API_BASE}/api/v1/auth/github/authorize?redirect_uri=${encodeURIComponent(redirectUri)}`
                    )
                    const data = await response.json()
                    
                    if (data.authorization_url) {
                      // Redirect to GitHub OAuth authorization page
                      window.location.href = data.authorization_url
                    } else {
                      console.error('Failed to get GitHub authorization URL')
                    }
                  } catch (error) {
                    console.error('GitHub login failed:', error)
                  }
                }}
                disabled={isLoading}
              >
                <span className="mr-2 text-lg">⚡</span>
                Continue with GitHub
              </Button>
            </form>
        </CardContent>

        <CardFooter className="flex flex-col space-y-2">
          <div className="text-sm text-center text-muted-foreground">
            Don't have an account?{' '}
            <Link href="/register" className="text-primary hover:underline">
              Sign up
            </Link>
          </div>
          <div className="text-sm text-center">
            <Link 
              href="/reset-password"
              className="text-muted-foreground hover:underline cursor-pointer"
            >
              Forgot your password?
            </Link>
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
