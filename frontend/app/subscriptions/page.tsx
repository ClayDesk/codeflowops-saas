'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Shield, 
  CreditCard, 
  Calendar,
  CheckCircle,
  XCircle,
  Clock,
  AlertTriangle,
  Loader2
} from 'lucide-react'
import Link from 'next/link'

interface SubscriptionData {
  id: string
  status: string
  plan: {
    product: string
    amount: number
    currency: string
    interval: string
  }
  current_period_end?: number
  trial_end?: number
  cancel_at_period_end: boolean
}

export default function SubscriptionsPage() {
  const { user, isAuthenticated, loading: authLoading, fetchUserProfile } = useAuth()
  const [subscription, setSubscription] = useState<SubscriptionData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Redirect to login if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      window.location.href = '/login'
    }
  }, [isAuthenticated, authLoading])

  // Fetch subscription data
  useEffect(() => {
    const fetchSubscriptionData = async () => {
      if (!isAuthenticated) return
      
      try {
        setLoading(true)
        setError(null)
        
        console.log('📊 Fetching subscription data...')
        const profileData = await fetchUserProfile()
        console.log('📊 Profile data received:', profileData)
        
        if (profileData?.subscription) {
          console.log('✅ Subscription found:', profileData.subscription)
          setSubscription(profileData.subscription as unknown as SubscriptionData)
        } else {
          console.log('ℹ️ No subscription found')
          setSubscription(null)
        }
      } catch (err) {
        console.error('❌ Error fetching subscription:', err)
        const errorMessage = err instanceof Error ? err.message : 'Unknown error'
        setError(`Failed to load subscription information: ${errorMessage}. Please try again or contact support.`)
      } finally {
        setLoading(false)
      }
    }

    if (isAuthenticated) {
      fetchSubscriptionData()
    }
  }, [isAuthenticated, fetchUserProfile])

  // Helper functions
  const getStatusIcon = (status: string) => {
    switch (status?.toLowerCase()) {
      case 'active':
        return <CheckCircle className="h-5 w-5 text-green-600" />
      case 'trialing':
        return <Clock className="h-5 w-5 text-blue-600" />
      case 'past_due':
        return <AlertTriangle className="h-5 w-5 text-yellow-600" />
      case 'canceled':
      case 'cancelled':
        return <XCircle className="h-5 w-5 text-red-600" />
      default:
        return <Shield className="h-5 w-5 text-gray-600" />
    }
  }

  const getStatusBadge = (status: string) => {
    const statusLower = status?.toLowerCase()
    const variants = {
      active: 'default',
      trialing: 'secondary',
      past_due: 'destructive',
      canceled: 'outline',
      cancelled: 'outline'
    } as const
    
    return (
      <Badge variant={variants[statusLower as keyof typeof variants] || 'outline'}>
        {status?.charAt(0).toUpperCase() + status?.slice(1) || 'Unknown'}
      </Badge>
    )
  }

  const formatAmount = (amount: number, currency: string = 'usd') => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency.toUpperCase(),
    }).format(amount / 100)
  }

  const formatDate = (timestamp: number) => {
    return new Date(timestamp).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric'
    })
  }

  // Show loading state
  if (authLoading || loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Loader2 className="h-8 w-8 animate-spin mx-auto mb-4" />
          <p className="text-muted-foreground">Loading subscription information...</p>
        </div>
      </div>
    )
  }

  // Show authentication required
  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <Shield className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
              <p className="text-muted-foreground mb-4">Please sign in to view your subscription.</p>
              <Button asChild>
                <Link href="/login">Sign In</Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
            Your Subscription
          </h1>
          <p className="text-gray-600 dark:text-gray-400 mt-2">
            Manage your CodeFlowOps subscription and view your plan details
          </p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert className="mb-6 border-red-200 bg-red-50 dark:border-red-800 dark:bg-red-950">
            <AlertTriangle className="h-4 w-4 text-red-600" />
            <AlertDescription className="text-red-800 dark:text-red-200">
              {error}
            </AlertDescription>
          </Alert>
        )}

        {/* Subscription Card */}
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <CreditCard className="h-5 w-5" />
              Current Plan
            </CardTitle>
            <CardDescription>
              Your subscription details and billing information
            </CardDescription>
          </CardHeader>
          <CardContent>
            {subscription ? (
              <div className="space-y-6">
                {/* Plan Overview */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">Plan</p>
                    <p className="text-2xl font-bold">
                      {subscription.plan.product}
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">Status</p>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(subscription.status)}
                      {getStatusBadge(subscription.status)}
                    </div>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">Price</p>
                    <p className="text-xl font-semibold">
                      {formatAmount(subscription.plan.amount, subscription.plan.currency)}
                      <span className="text-sm font-normal text-muted-foreground">
                        /{subscription.plan.interval}
                      </span>
                    </p>
                  </div>
                  <div className="space-y-2">
                    <p className="text-sm font-medium text-muted-foreground">Subscription ID</p>
                    <p className="text-sm font-mono bg-muted px-2 py-1 rounded">
                      {subscription.id}
                    </p>
                  </div>
                </div>

                {/* Billing Information */}
                {subscription.current_period_end && (
                  <div className="pt-4 border-t">
                    <div className="flex items-center gap-2 mb-2">
                      <Calendar className="h-4 w-4 text-muted-foreground" />
                      <p className="text-sm font-medium text-muted-foreground">Billing Information</p>
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <p className="text-sm text-muted-foreground">Next billing date</p>
                        <p className="font-medium">
                          {formatDate(subscription.current_period_end)}
                        </p>
                      </div>
                      {subscription.trial_end && (
                        <div>
                          <p className="text-sm text-muted-foreground">Trial ends</p>
                          <p className="font-medium text-blue-600">
                            {formatDate(subscription.trial_end)}
                          </p>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Status-specific messages */}
                {subscription.status === 'trialing' && (
                  <Alert className="border-blue-200 bg-blue-50 dark:border-blue-800 dark:bg-blue-950">
                    <Clock className="h-4 w-4 text-blue-600" />
                    <AlertDescription className="text-blue-800 dark:text-blue-200">
                      You're currently on a free trial. Enjoy full access to all features!
                    </AlertDescription>
                  </Alert>
                )}

                {subscription.cancel_at_period_end && (
                  <Alert className="border-orange-200 bg-orange-50 dark:border-orange-800 dark:bg-orange-950">
                    <AlertTriangle className="h-4 w-4 text-orange-600" />
                    <AlertDescription className="text-orange-800 dark:text-orange-200">
                      Your subscription will be cancelled at the end of the current billing period.
                    </AlertDescription>
                  </Alert>
                )}
              </div>
            ) : (
              /* No Subscription State */
              <div className="text-center py-8">
                <Shield className="h-16 w-16 mx-auto mb-4 text-muted-foreground" />
                <h3 className="text-lg font-semibold mb-2">No Active Subscription</h3>
                <p className="text-muted-foreground mb-4">
                  You don't currently have an active subscription. Upgrade to Pro to unlock all features.
                </p>
                <Button asChild>
                  <Link href="/pricing">View Pricing Plans</Link>
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Navigation Links */}
        <div className="flex flex-wrap gap-4">
          <Button variant="outline" asChild>
            <Link href="/profile">
              Back to Profile
            </Link>
          </Button>
          {!subscription && (
            <Button asChild>
              <Link href="/pricing">
                View Pricing
              </Link>
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}