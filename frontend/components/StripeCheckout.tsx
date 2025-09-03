'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Loader2, CheckCircle, CreditCard, Shield, Clock, Star, LogIn } from 'lucide-react'
import { useStripe } from '@/hooks/use-stripe'
import { useAuth } from '@/lib/auth-context'
import { useRouter } from 'next/navigation'

interface StripeCheckoutProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export function StripeCheckout({ onSuccess, onCancel }: StripeCheckoutProps) {
  const [isComplete, setIsComplete] = useState(false)
  const [subscriptionData, setSubscriptionData] = useState<any>(null)
  const { isAuthenticated, loading: authLoading, user } = useAuth()
  const router = useRouter()

  const { createSubscription, loading, error, clearError } = useStripe({
    onSuccess: (result) => {
      // Only show success state if we have a completed subscription WITHOUT a checkout URL
      // If checkout_url exists, the user needs to complete payment on Stripe first
      if (result.subscription && !result.subscription.checkout_url) {
        setSubscriptionData(result.subscription)
        setIsComplete(true)
        onSuccess?.()
      }
      // If checkout_url exists, the hook will redirect to Stripe automatically
    },
    onError: (error) => {
      console.error('Subscription error:', error)
    }
  })

  const handleStartTrial = async () => {
    if (!isAuthenticated || !user) {
      router.push('/login?redirect=/pricing')
      return
    }

    await createSubscription({
      email: user.email,
      name: user.name || user.full_name || user.username,
      trialDays: 14
    })
  }

  const handleTryAgain = () => {
    setIsComplete(false)
    setSubscriptionData(null)
    clearError()
  }

  // Show login prompt if not authenticated
  if (!authLoading && !isAuthenticated) {
    return (
      <Card className="max-w-lg mx-auto shadow-xl">
        <CardHeader className="text-center pb-6">
          <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
            <LogIn className="w-6 h-6 text-blue-600" />
          </div>
          <CardTitle className="text-2xl font-bold">Sign In Required</CardTitle>
          <CardDescription>
            Please sign in to start your free trial
          </CardDescription>
        </CardHeader>

        <CardContent className="space-y-4">
          <div className="flex gap-3">
            <Button 
              className="flex-1 bg-blue-600 hover:bg-blue-700"
              onClick={() => router.push('/login?redirect=/pricing')}
            >
              Sign In
            </Button>
            <Button 
              variant="outline" 
              className="flex-1"
              onClick={() => router.push('/register?redirect=/pricing')}
            >
              Sign Up
            </Button>
          </div>

          {onCancel && (
            <Button 
              variant="ghost" 
              onClick={onCancel}
              className="w-full"
            >
              Back to Pricing
            </Button>
          )}
        </CardContent>
      </Card>
    )
  }

  // Success state
  if (isComplete && subscriptionData) {
    return (
      <Card className="max-w-lg mx-auto shadow-xl border-green-200">
        <CardHeader className="text-center pb-4">
          <div className="mx-auto w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mb-4">
            <CheckCircle className="w-8 h-8 text-green-600" />
          </div>
          <CardTitle className="text-2xl font-bold text-green-800">Welcome to CodeFlowOps Pro!</CardTitle>
          <CardDescription className="text-green-600">
            Your 14-day free trial has started successfully
          </CardDescription>
        </CardHeader>
        
        <CardContent className="space-y-6">
          <div className="bg-green-50 p-4 rounded-lg border border-green-200">
            <h3 className="font-semibold text-green-800 mb-3">Subscription Details</h3>
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <span className="text-green-700">Plan:</span>
                <span className="font-medium">CodeFlowOps Pro</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Status:</span>
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  Active Trial
                </Badge>
              </div>
            </div>
          </div>

          <div className="flex gap-3">
            <Button 
              className="flex-1 bg-green-600 hover:bg-green-700"
              onClick={() => window.location.href = '/dashboard'}
            >
              Go to Dashboard
            </Button>
            <Button 
              variant="outline" 
              onClick={handleTryAgain}
              className="border-green-200 text-green-700 hover:bg-green-50"
            >
              Create Another
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Authenticated user checkout flow
  return (
    <Card className="max-w-lg mx-auto shadow-xl">
      <CardHeader className="text-center pb-6">
        <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
          <CreditCard className="w-6 h-6 text-blue-600" />
        </div>
        <CardTitle className="text-2xl font-bold">Start Your Free Trial</CardTitle>
        <CardDescription>
          Hi {user?.name || user?.username}! Ready to start your 14-day free trial?
        </CardDescription>
        
        {/* User Info */}
        {user && (
          <div className="mt-4 p-4 bg-gray-50 rounded-lg border">
            <div className="text-sm text-gray-700">
              <div className="flex justify-between">
                <span>Email:</span>
                <span className="font-medium">{user.email}</span>
              </div>
              <div className="flex justify-between">
                <span>Name:</span>
                <span className="font-medium">{user.name || user.full_name || user.username}</span>
              </div>
            </div>
          </div>
        )}
      </CardHeader>

      <CardContent className="space-y-6">
        {error && (
          <Alert variant="destructive">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Pricing Summary */}
        <div className="bg-gray-50 p-4 rounded-lg border">
          <div className="flex justify-between items-center mb-2">
            <span className="text-sm text-gray-600">CodeFlowOps Pro</span>
            <span className="font-semibold">$19/month</span>
          </div>
          <div className="flex justify-between items-center text-green-600">
            <span className="text-sm flex items-center">
              <Clock className="w-4 h-4 mr-1" />
              14-day free trial
            </span>
            <span className="font-semibold">$0 today</span>
          </div>
          <div className="text-xs text-gray-500 mt-2">
            Trial starts today. You&apos;ll add payment details on Stripe&apos;s secure checkout page.
          </div>
        </div>

        <Button 
          onClick={handleStartTrial} 
          className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-3"
          disabled={loading || authLoading}
        >
          {loading ? (
            <>
              <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              Redirecting to checkout...
            </>
          ) : (
            'Continue to Payment Setup'
          )}
        </Button>

        {/* Security & Trust */}
        <div className="text-center">
          <div className="flex items-center justify-center text-xs text-gray-500 mb-2">
            <Shield className="w-3 h-3 mr-1" />
            Secured by Stripe • SSL Encrypted
          </div>
          <p className="text-xs text-gray-500">
            You&apos;ll enter payment details on Stripe&apos;s secure checkout page
          </p>
        </div>

        {onCancel && (
          <Button 
            type="button" 
            variant="ghost" 
            onClick={onCancel}
            className="w-full"
            disabled={loading}
          >
            Back to Pricing
          </Button>
        )}
      </CardContent>
    </Card>
  )
}

export default StripeCheckout
