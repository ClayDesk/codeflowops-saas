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
        // Capture next URL BEFORE clearing search params
        const nextUrl = searchParams.get('next') || '/profile'
        
        const success = searchParams.get('success')
        const error = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')
        const loginToken = searchParams.get('login_token')
        const token = searchParams.get('token') // Direct token from simplified flow
        const authenticated = searchParams.get('authenticated')

        if (error) {
          setStatus('error')
          setMessage(errorDescription || error || 'Authentication failed')
          return
        }

        // Handle direct token (simplified flow)
        if (token) {
          try {
            // Verify the token with backend
            const apiBase = (process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com').replace(/\/+$/, '');
            const verifyRes = await fetch(`${apiBase}/github/verify`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ token }),
            });

            if (verifyRes.ok) {
              const userData = await verifyRes.json();
              // Store token and redirect
              localStorage.setItem('auth_token', token);
              localStorage.setItem('codeflowops_access_token', token);
              localStorage.setItem('codeflowops_user', JSON.stringify(userData.user));
              
              setStatus('success');
              setMessage('Authentication successful! Redirecting...');
              
              setTimeout(() => {
                window.location.replace(nextUrl);
              }, 1000);
              return;
            }
          } catch (err) {
            console.error('Token verification failed:', err);
          }
        }

        // Handle login token exchange flow
        if (success === 'true' && loginToken) {
          // Exchange login token for real credentials with polling support
          const apiBase = (process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com').replace(/\/+$/, '');

          let tries = 0;
          let data: any = null;
          while (tries < 20) { // ~10 seconds total
            const res = await fetch(`${apiBase}/session/consume`, {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ token: loginToken }),
            });
            
            if (!res.ok) {
              data = await res.json();
              setStatus('error');
              setMessage(data?.message || `Auth exchange failed (${res.status})`);
              return;
            }
            
            data = await res.json();
            
            if (res.status === 202 && data?.pending) {
              await new Promise(r => setTimeout(r, 500));
              tries += 1;
              continue;
            }
            break;
          }

          if (data && data.access_token) {
            setStatus('success');
            setMessage('Authentication successful! Redirecting...');
            
            // Store token and update auth context
            localStorage.setItem('auth_token', data.access_token);
            localStorage.setItem('codeflowops_access_token', data.access_token);
            if (data.refresh_token) {
              localStorage.setItem('codeflowops_refresh_token', data.refresh_token);
            }
            if (data.user) {
              localStorage.setItem('codeflowops_user', JSON.stringify(data.user));
            }
            
            setTimeout(() => {
              window.location.replace(nextUrl);
            }, 600);
          } else if (data?.error) {
            setStatus('error');
            setMessage(data.error);
          } else {
            setStatus('error');
            setMessage('Authentication failed - no token received');
          }
        } else if (authenticated === 'true') {
          // Simple authenticated redirect
          setStatus('success');
          setMessage('Authentication successful! Redirecting...');
          
          setTimeout(() => {
            window.location.replace(nextUrl);
          }, 600);
        } else {
          setStatus('error');
          setMessage('No authentication data received');
        }
      } catch (err) {
        console.error('Auth callback error:', err);
        setStatus('error');
        setMessage('Authentication failed due to an error');
      }
    };

    handleCallback();
  }, [searchParams, router]);

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
                <span>Authentication Successful</span>
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
          <p className="text-gray-600 dark:text-gray-400">
            {message}
          </p>
          
          {status === 'loading' && (
            <div className="space-y-2">
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-blue-600 h-2 rounded-full animate-pulse" style={{ width: '60%' }}></div>
              </div>
              <p className="text-sm text-gray-500">
                Please wait while we complete your authentication...
              </p>
            </div>
          )}
          
          {status === 'error' && (
            <div className="space-y-3">
              <p className="text-sm text-gray-500">
                Something went wrong during authentication. Please try again.
              </p>
              <Link 
                href="/login"
                className="inline-flex items-center px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors"
              >
                Back to Login
              </Link>
            </div>
          )}
          
          {status === 'success' && (
            <div className="space-y-2">
              <p className="text-sm text-gray-500">
                Redirecting you to your dashboard...
              </p>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div className="bg-green-600 h-2 rounded-full animate-pulse" style={{ width: '100%' }}></div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

export default function AuthCallback() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
      </div>
    }>
      <AuthCallbackContent />
    </Suspense>
  )
}
