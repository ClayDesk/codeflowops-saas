'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Loader2, CheckCircle, CreditCard, Shield, Clock, Star } from 'lucide-react'
import { useStripe } from '@/hooks/use-stripe'

interface StripeCheckoutProps {
  onSuccess?: () => void
  onCancel?: () => void
}

export function StripeCheckout({ onSuccess, onCancel }: StripeCheckoutProps) {
  const [email, setEmail] = useState('')
  const [name, setName] = useState('')
  const [isComplete, setIsComplete] = useState(false)
  const [subscriptionData, setSubscriptionData] = useState<any>(null)

  const { createSubscription, loading, error, clearError } = useStripe({
    onSuccess: (result) => {
      setSubscriptionData(result.subscription)
      setIsComplete(true)
      onSuccess?.()
    },
    onError: (error) => {
      console.error('Subscription error:', error)
    }
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!email) return

    await createSubscription({
      email,
      name: name || undefined,
      trialDays: 14
    })
  }

  const handleTryAgain = () => {
    setIsComplete(false)
    setSubscriptionData(null)
    clearError()
  }

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
                <span className="text-green-700">Trial Period:</span>
                <span className="font-medium">14 days</span>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Status:</span>
                <Badge variant="secondary" className="bg-green-100 text-green-800">
                  Active Trial
                </Badge>
              </div>
              <div className="flex justify-between">
                <span className="text-green-700">Customer ID:</span>
                <span className="font-mono text-xs">{subscriptionData.customer_id}</span>
              </div>
            </div>
          </div>

          <div className="space-y-3">
            <h4 className="font-semibold text-gray-800">What&apos;s Next?</h4>
            <ul className="space-y-2 text-sm text-gray-600">
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                Access your dashboard and start analyzing repositories
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                Explore AI-powered deployment recommendations
              </li>
              <li className="flex items-start">
                <CheckCircle className="w-4 h-4 text-green-500 mr-2 mt-0.5 flex-shrink-0" />
                Set up your first automated deployment
              </li>
            </ul>
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

  return (
    <Card className="max-w-lg mx-auto shadow-xl">
      <CardHeader className="text-center pb-6">
        <div className="mx-auto w-12 h-12 bg-blue-100 rounded-full flex items-center justify-center mb-4">
          <CreditCard className="w-6 h-6 text-blue-600" />
        </div>
        <CardTitle className="text-2xl font-bold">Start Your Free Trial</CardTitle>
        <CardDescription>
          Get 14 days free, then $12/month. Enter your details to continue to secure payment setup.
        </CardDescription>
        
        {/* Trial Benefits */}
        <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
          <div className="flex items-center justify-center mb-3">
            <Star className="w-5 h-5 text-yellow-500 mr-2" />
            <span className="text-sm font-semibold text-blue-800">Trial Includes</span>
          </div>
          <div className="grid grid-cols-2 gap-2 text-xs text-blue-700">
            <div className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              Unlimited projects
            </div>
            <div className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              AI recommendations
            </div>
            <div className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              Multi-cloud support
            </div>
            <div className="flex items-center">
              <CheckCircle className="w-3 h-3 mr-1" />
              Priority support
            </div>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-6">
          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="space-y-4">
            <div>
              <Label htmlFor="email" className="text-sm font-medium">
                Email Address *
              </Label>
              <Input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                required
                className="mt-1"
                disabled={loading}
              />
            </div>

            <div>
              <Label htmlFor="name" className="text-sm font-medium">
                Full Name (Optional)
              </Label>
              <Input
                id="name"
                type="text"
                value={name}
                onChange={(e) => setName(e.target.value)}
                placeholder="John Doe"
                className="mt-1"
                disabled={loading}
              />
            </div>
          </div>

          {/* Pricing Summary */}
          <div className="bg-gray-50 p-4 rounded-lg border">
            <div className="flex justify-between items-center mb-2">
              <span className="text-sm text-gray-600">CodeFlowOps Pro</span>
              <span className="font-semibold">$12/month</span>
            </div>
            <div className="flex justify-between items-center text-green-600">
              <span className="text-sm flex items-center">
                <Clock className="w-4 h-4 mr-1" />
                14-day free trial
              </span>
              <span className="font-semibold">$0 today</span>
            </div>
            <div className="text-xs text-gray-500 mt-2">
              Your trial starts today. You&apos;ll be charged $12/month after 14 days.
            </div>
          </div>

          <Button 
            type="submit" 
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-3"
            disabled={loading || !email}
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Redirecting to checkout...
              </>
            ) : (
              'Continue to Payment'
            )}
          </Button>

          {/* Security & Trust */}
          <div className="text-center">
            <div className="flex items-center justify-center text-xs text-gray-500 mb-2">
              <Shield className="w-3 h-3 mr-1" />
              Secured by Stripe • SSL Encrypted
            </div>
            <p className="text-xs text-gray-500">
              You'll enter payment details on Stripe's secure checkout page
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
        </form>
      </CardContent>
    </Card>
  )
}

export default StripeCheckout
