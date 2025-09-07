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
            // Store token in secure cookie instead of localStorage
            document.cookie = `auth_token=${token}; path=/; secure; samesite=strict; max-age=86400`; // 24 hours
            document.cookie = `codeflowops_access_token=${token}; path=/; secure; samesite=strict; max-age=86400`;

            // Store minimal user info in session storage temporarily
            sessionStorage.setItem('codeflowops_access_token', token);

            setStatus('success');
            setMessage('Authentication successful! Redirecting...');

            setTimeout(() => {
              window.location.replace(nextUrl);
            }, 1000);
            return;
          } catch (err) {
            console.error('Token storage failed:', err);
          }
        }

        // Handle login token exchange flow
        if (success === 'true' && loginToken) {
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

            // Store authentication data in server-side session instead of localStorage
            // Set session cookie for server-side session management
            document.cookie = `auth_token=${data.access_token}; path=/; secure; samesite=strict; max-age=86400`; // 24 hours
            if (data.refresh_token) {
              document.cookie = `refresh_token=${data.refresh_token}; path=/; secure; samesite=strict; max-age=604800`; // 7 days
            }

            // Store user data in session storage (temporary, will be replaced by server session)
            if (data.user) {
              sessionStorage.setItem('codeflowops_user', JSON.stringify(data.user));
              // Also store minimal user info in cookie for server-side access
              document.cookie = `user_id=${data.user.user_id || data.user.id}; path=/; secure; samesite=strict; max-age=86400`;
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
