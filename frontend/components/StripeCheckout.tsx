'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, CheckCircle, CreditCard } from 'lucide-react'
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
    
    if (!email) {
      return
    }

    clearError()
    
    try {
      await createSubscription({
        email,
        name: name || undefined,
        trialDays: 14
      })
    } catch (error) {
      // Error is handled by the hook
    }
  }

  if (isComplete && subscriptionData) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <CardTitle className="text-green-900">Welcome to CodeFlowOps Pro!</CardTitle>
          <CardDescription>
            Your 14-day free trial has started. You won't be charged until the trial ends.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="p-4 bg-blue-50 rounded-lg text-sm">
            <p><strong>Trial ends:</strong> {new Date(subscriptionData.trial_end * 1000).toLocaleDateString()}</p>
            <p><strong>Plan:</strong> Pro ($12/month after trial)</p>
            <p><strong>Status:</strong> {subscriptionData.status}</p>
          </div>
          <Button onClick={() => window.location.href = '/dashboard'} className="w-full">
            Go to Dashboard
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <CreditCard className="h-5 w-5" />
          Start Your Free Trial
        </CardTitle>
        <CardDescription>
          Get 14 days free, then $12/month. Cancel anytime.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="email">Email Address</Label>
            <Input
              id="email"
              type="email"
              placeholder="your.email@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
            />
          </div>
          
          <div className="space-y-2">
            <Label htmlFor="name">Full Name (Optional)</Label>
            <Input
              id="name"
              type="text"
              placeholder="Your Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>

          {error && (
            <Alert variant="destructive">
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          <div className="p-3 bg-blue-50 rounded text-sm text-blue-800">
            <strong>Free Trial:</strong> 14 days free, no payment required now. 
            You'll be charged $12/month after your trial ends. Cancel anytime.
          </div>

          <div className="flex gap-3">
            {onCancel && (
              <Button 
                type="button" 
                variant="outline" 
                onClick={onCancel}
                className="flex-1"
                disabled={loading}
              >
                Cancel
              </Button>
            )}
            <Button 
              type="submit" 
              disabled={loading || !email}
              className="flex-1"
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Starting Trial...
                </>
              ) : (
                'Start Free Trial'
              )}
            </Button>
          </div>

          <p className="text-xs text-gray-500 text-center">
            By starting your trial, you agree to our Terms of Service and Privacy Policy.
          </p>
        </form>
      </CardContent>
    </Card>
  )
}
