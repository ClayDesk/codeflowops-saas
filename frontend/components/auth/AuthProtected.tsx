import React from 'react'
import { useAuthGuard } from '@/hooks/use-auth-guard'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { Shield, UserPlus } from 'lucide-react'
import Link from 'next/link'

interface AuthProtectedProps {
  children: React.ReactNode
  fallback?: React.ReactNode
  redirectTo?: string
  requiresAuth?: boolean
}

/**
 * Higher-Order Component that protects deployment functionality with authentication
 */
export function AuthProtected({ 
  children, 
  fallback, 
  redirectTo = '/register',
  requiresAuth = true 
}: AuthProtectedProps) {
  const { isAuthenticated, loading } = useAuthGuard(requiresAuth ? redirectTo : undefined)

  // Show loading skeleton while checking authentication
  if (loading) {
    return fallback || (
      <div className="space-y-6 p-6">
        <Skeleton className="w-64 h-8" />
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
        <Skeleton className="w-full h-96" />
      </div>
    )
  }

  // Show auth prompt if not authenticated
  if (requiresAuth && !isAuthenticated) {
    return (
      <div className="min-h-[60vh] flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="p-8 text-center space-y-6">
            <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900 rounded-full flex items-center justify-center mx-auto">
              <Shield className="w-8 h-8 text-blue-600 dark:text-blue-400" />
            </div>
            
            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-gray-900 dark:text-white">
                Authentication Required
              </h2>
              <p className="text-gray-600 dark:text-gray-300">
                Please sign up or sign in to access deployment features and manage your projects.
              </p>
            </div>

            <div className="space-y-3">
              <Link href="/register" className="w-full block">
                <Button className="w-full" size="lg">
                  <UserPlus className="w-4 h-4 mr-2" />
                  Create Free Account
                </Button>
              </Link>
              <Link href="/login" className="w-full block">
                <Button variant="outline" className="w-full" size="lg">
                  Sign In to Existing Account
                </Button>
              </Link>
            </div>

            <p className="text-sm text-gray-500">
              🚀 Deploy unlimited projects • ⚡ 5-minute setup • 🔒 Enterprise security
            </p>
          </CardContent>
        </Card>
      </div>
    )
  }

  // Render protected content
  return <>{children}</>
}

/**
 * Hook for conditional authentication protection
 */
export function useAuthProtection(requiresAuth: boolean = true) {
  const { isAuthenticated, loading } = useAuthGuard(requiresAuth ? '/register' : undefined)
  
  return {
    isAuthenticated,
    loading,
    shouldShowContent: !requiresAuth || isAuthenticated,
    shouldShowAuthPrompt: requiresAuth && !loading && !isAuthenticated,
    shouldShowLoading: loading
  }
}
