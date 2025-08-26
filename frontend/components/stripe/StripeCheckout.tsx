'use client'

import React, { useState, useEffect } from 'react'
import { loadStripe } from '@stripe/stripe-js'
import { Elements, useStripe, useElements, PaymentElement } from '@stripe/react-stripe-js'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Loader2, CheckCircle, AlertCircle, CreditCard } from 'lucide-react'
import { useStripePayment } from '@/hooks/use-stripe-payment'

// Initialize Stripe
const stripePromise = loadStripe(process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY!)

interface CheckoutFormProps {
  planTier: string
  planName: string
  planPrice: string
  planFeatures: string[]
  trialDays?: number
  onSuccess?: () => void
  onCancel?: () => void
}

function CheckoutForm({ planTier, planName, planPrice, planFeatures, trialDays, onSuccess, onCancel }: CheckoutFormProps) {
  const stripe = useStripe()
  const elements = useElements()
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [isComplete, setIsComplete] = useState(false)

  const handleSubmit = async (event: React.FormEvent) => {
    event.preventDefault()

    if (!stripe || !elements) {
      return
    }

    setIsLoading(true)
    setMessage(null)

    const { error } = await stripe.confirmPayment({
      elements,
      confirmParams: {
        return_url: `${window.location.origin}/profile?tab=subscription&success=true&plan=${planTier}`,
      },
    })

    if (error) {
      if (error.type === "card_error" || error.type === "validation_error") {
        setMessage(error.message!)
      } else {
        setMessage("An unexpected error occurred.")
      }
    } else {
      setIsComplete(true)
      onSuccess?.()
    }

    setIsLoading(false)
  }

  if (isComplete) {
    return (
      <Card className="w-full max-w-md mx-auto">
        <CardHeader className="text-center">
          <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-full bg-green-100">
            <CheckCircle className="h-6 w-6 text-green-600" />
          </div>
          <CardTitle className="text-green-900">Payment Successful!</CardTitle>
          <CardDescription>
            Welcome to CodeFlowOps {planName}! Your subscription is now active.
          </CardDescription>
        </CardHeader>
        <CardContent className="text-center">
          <Button onClick={() => window.location.href = '/profile?tab=subscription'} className="w-full">
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
          Complete Your Subscription
        </CardTitle>
        <CardDescription>
          Subscribe to {planName} for {planPrice}/month
          {trialDays && trialDays > 0 && (
            <Badge variant="outline" className="ml-2">
              {trialDays} days free trial
            </Badge>
          )}
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {/* Plan Summary */}
        <div className="border rounded-lg p-4 bg-gray-50 dark:bg-gray-900">
          <h4 className="font-semibold mb-2">{planName} Plan</h4>
          <div className="text-2xl font-bold mb-2">{planPrice}<span className="text-sm font-normal">/month</span></div>
          <ul className="space-y-1 text-sm">
            {planFeatures.map((feature, index) => (
              <li key={index} className="flex items-center gap-2">
                <CheckCircle className="h-3 w-3 text-green-500" />
                {feature}
              </li>
            ))}
          </ul>
          {trialDays && trialDays > 0 && (
            <div className="mt-3 p-2 bg-blue-50 dark:bg-blue-900/20 rounded text-sm text-blue-800 dark:text-blue-200">
              <strong>Free Trial:</strong> You won't be charged for {trialDays} days. Cancel anytime during the trial.
            </div>
          )}
        </div>

        {/* Payment Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <PaymentElement />
          
          {message && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}

          <div className="flex gap-3">
            <Button 
              type="button" 
              variant="outline" 
              onClick={onCancel}
              className="flex-1"
              disabled={isLoading}
            >
              Cancel
            </Button>
            <Button 
              type="submit" 
              disabled={isLoading || !stripe || !elements}
              className="flex-1"
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Processing...
                </>
              ) : trialDays && trialDays > 0 ? (
                'Start Free Trial'
              ) : (
                'Subscribe Now'
              )}
            </Button>
          </div>
        </form>

        <div className="text-xs text-gray-500 text-center">
          Secure payment powered by Stripe. Your payment information is encrypted and secure.
        </div>
      </CardContent>
    </Card>
  )
}

interface StripeCheckoutProps {
  clientSecret: string
  planTier: string
  planName: string
  planPrice: string
  planFeatures: string[]
  trialDays?: number
  onSuccess?: () => void
  onCancel?: () => void
}

export function StripeCheckout({
  clientSecret,
  planTier,
  planName,
  planPrice,
  planFeatures,
  trialDays,
  onSuccess,
  onCancel
}: StripeCheckoutProps) {
  const options = {
    clientSecret,
    appearance: {
      theme: 'stripe' as const,
      variables: {
        colorPrimary: '#3b82f6',
        colorBackground: '#ffffff',
        colorText: '#1f2937',
        colorDanger: '#ef4444',
        fontFamily: 'Inter, system-ui, sans-serif',
        spacingUnit: '4px',
        borderRadius: '8px',
      },
    },
  }

  return (
    <Elements options={options} stripe={stripePromise}>
      <CheckoutForm
        planTier={planTier}
        planName={planName}
        planPrice={planPrice}
        planFeatures={planFeatures}
        trialDays={trialDays}
        onSuccess={onSuccess}
        onCancel={onCancel}
      />
    </Elements>
  )
}

// Quick checkout button component for pricing cards
interface QuickCheckoutButtonProps {
  planTier: string
  planName: string
  planPrice: string
  planFeatures: string[]
  trialDays?: number
  pricingContext?: Record<string, any>
  disabled?: boolean
  children: React.ReactNode
}

export function QuickCheckoutButton({
  planTier,
  planName,
  planPrice,
  planFeatures,
  trialDays,
  pricingContext,
  disabled,
  children
}: QuickCheckoutButtonProps) {
  const [showCheckout, setShowCheckout] = useState(false)
  const [clientSecret, setClientSecret] = useState<string | null>(null)
  const { createSubscription, loading, error } = useStripePayment({
    onError: (error) => {
      console.error('Subscription creation failed:', error)
    }
  })

  const handleStartCheckout = async () => {
    try {
      const result = await createSubscription({
        planTier,
        pricingContext,
        trialDays
      })

      if (result.requires_payment && result.client_secret) {
        setClientSecret(result.client_secret)
        setShowCheckout(true)
      } else {
        // Free trial or free plan - redirect to success
        window.location.href = `/profile?tab=subscription&success=true&plan=${planTier}`
      }
    } catch (err) {
      console.error('Failed to start checkout:', err)
    }
  }

  if (showCheckout && clientSecret) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
        <div className="max-w-lg w-full">
          <StripeCheckout
            clientSecret={clientSecret}
            planTier={planTier}
            planName={planName}
            planPrice={planPrice}
            planFeatures={planFeatures}
            trialDays={trialDays}
            onSuccess={() => {
              setShowCheckout(false)
              window.location.href = `/profile?tab=subscription&success=true&plan=${planTier}`
            }}
            onCancel={() => setShowCheckout(false)}
          />
        </div>
      </div>
    )
  }

  return (
    <>
      <Button
        onClick={handleStartCheckout}
        disabled={disabled || loading}
        className="w-full"
      >
        {loading ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Processing...
          </>
        ) : (
          children
        )}
      </Button>
      
      {error && (
        <Alert variant="destructive" className="mt-2">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}
    </>
  )
}
