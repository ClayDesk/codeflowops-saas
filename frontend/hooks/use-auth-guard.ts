import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'

/**
 * Hook to protect routes - redirects to login if user is not authenticated
 */
export function useAuthGuard(redirectTo = '/login') {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push(redirectTo)
    }
  }, [loading, isAuthenticated, router, redirectTo])

  return { isAuthenticated, loading }
}

/**
 * Hook to redirect authenticated users away from auth pages
 */
export function useGuestGuard(redirectTo = '/deploy') {
  const { isAuthenticated, loading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!loading && isAuthenticated) {
      router.push(redirectTo)
    }
  }, [loading, isAuthenticated, router, redirectTo])

  return { isAuthenticated, loading }
}

/**
 * Hook for conditional rendering based on auth status
 */
export function useAuthState() {
  const { user, isAuthenticated, loading } = useAuth()
  
  return {
    user,
    isAuthenticated,
    loading,
    isGuest: !loading && !isAuthenticated,
    isLoggedIn: !loading && isAuthenticated
  }
}
