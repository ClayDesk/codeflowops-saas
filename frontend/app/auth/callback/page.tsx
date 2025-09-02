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
          const loginToken = searchParams.get('login_token')
          const provider = searchParams.get('provider')

          if (loginToken) {
            // Exchange login token for real credentials with polling support
            const apiBase = (process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com').replace(/\/+$/, '');

            let tries = 0;
            let data: any = null;
            while (tries < 20) { // ~10 seconds total
              const res = await fetch(`${apiBase}/api/v1/auth/session/consume`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ token: loginToken }),
              });
              data = await res.json();
              if (res.status === 202 && data?.pending) {
                await new Promise(r => setTimeout(r, 500));
                tries += 1;
                continue;
              }
              if (!res.ok) {
                setStatus('error');
                setMessage(data?.message || `Auth exchange failed (${res.status})`);
                return;
              }
              break;
            }

            if (!data?.success || !data?.user || !data?.access_token) {
              setStatus('error');
              setMessage(data?.message || 'Invalid authentication response');
              return;
            }

            // Store auth data manually for OAuth users since login() expects username/password
            if (typeof window !== 'undefined') {
              localStorage.setItem('codeflowops_access_token', data.access_token)
              if (data.refresh_token) {
                localStorage.setItem('codeflowops_refresh_token', data.refresh_token)
              }
              
              // Create user object
              const userData = {
                id: data.user.user_id,
                email: data.user.email,
                name: data.user.full_name || data.user.username,
                username: data.user.username,
                provider: 'github'
              }
              
              localStorage.setItem('codeflowops_user', JSON.stringify(userData))
            }

            setStatus('success')
            setMessage('Authentication successful! Redirecting...')

            // Redirect to dashboard after a short delay
            setTimeout(() => {
              router.push('/deploy')
            }, 2000)
          } else {
            setStatus('error')
            setMessage('No login token provided')
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
  }, [searchParams, router])

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
