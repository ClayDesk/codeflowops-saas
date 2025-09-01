'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2, CheckCircle, XCircle } from 'lucide-react'
import Link from 'next/link'

function AuthCallbackContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuth()
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [message, setMessage] = useState('')

  useEffect(() => {
    const handleCallback = async () => {
      try {
        const success = searchParams.get('success')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        if (error) {
          setStatus('error')
          setMessage(errorDescription || error || 'Authentication failed')
          return
        }

        if (success === 'true') {
          const userId = searchParams.get('user_id')
          const email = searchParams.get('email')
          const username = searchParams.get('username')
          const accessToken = searchParams.get('access_token')
          const cognitoIntegrated = searchParams.get('cognito_integrated')

          if (accessToken && email) {
            // Store user data in auth context
            const userData = {
              id: userId,
              email: email,
              username: username,
              accessToken: accessToken,
              cognitoIntegrated: cognitoIntegrated === 'true'
            }

            setStatus('success')
            setMessage('Authentication successful! Redirecting...')

            // Redirect to dashboard after a short delay
            setTimeout(() => {
              router.push('/deploy')
            }, 2000)
          } else {
            setStatus('error')
            setMessage('Invalid authentication response')
          }
        } else {
          setStatus('error')
          setMessage('Authentication failed')
        }
      } catch (err) {
        console.error('Auth callback error:', err)
        setStatus('error')
        setMessage('An error occurred during authentication')
      }
    }

    handleCallback()
  }, [searchParams, router, login])

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="flex items-center justify-center space-x-2">
            {status === 'loading' && (
              <>
                <Loader2 className="h-6 w-6 animate-spin text-blue-600" />
                <span>Processing Authentication...</span>
              </>
            )}
            {status === 'success' && (
              <>
                <CheckCircle className="h-6 w-6 text-green-600" />
                <span>Authentication Successful!</span>
              </>
            )}
            {status === 'error' && (
              <>
                <XCircle className="h-6 w-6 text-red-600" />
                <span>Authentication Failed</span>
              </>
            )}
          </CardTitle>
        </CardHeader>
        <CardContent className="text-center space-y-4">
          <p className="text-gray-600 dark:text-gray-300">
            {message}
          </p>
          
          {status === 'success' && (
            <div className="space-y-2">
              <p className="text-sm text-green-600">
                ✅ Successfully logged in with GitHub
              </p>
              <p className="text-sm text-green-600">
                ✅ Account created in AWS Cognito
              </p>
              <p className="text-sm text-gray-500">
                Redirecting to dashboard...
              </p>
            </div>
          )}

          {status === 'error' && (
            <div className="space-y-4">
              <Link 
                href="/login"
                className="inline-block bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 transition-colors"
              >
                Try Again
              </Link>
            </div>
          )}

          {status === 'loading' && (
            <div className="space-y-2">
              <p className="text-sm text-gray-500">
                Please wait while we complete your authentication...
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default function AuthCallbackPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="flex items-center space-x-2">
          <Loader2 className="h-6 w-6 animate-spin" />
          <span>Loading...</span>
        </div>
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  )
}
