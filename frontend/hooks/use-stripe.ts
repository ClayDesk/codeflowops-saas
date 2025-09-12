/**
 * Simple Stripe Hook
 * Handles subscription creation
 */

import { useState } from 'react'

interface UseStripeOptions {
  onSuccess?: (result: any) => void
  onError?: (error: string) => void
}

interface CreateSubscriptionParams {
  email: string
  name?: string
  trialDays?: number
}

export function useStripe({ onSuccess, onError }: UseStripeOptions = {}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'

  const createSubscription = async (params: CreateSubscriptionParams) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/payments/create-subscription`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          email: params.email,
          name: params.name,
          trial_days: params.trialDays || 0
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create checkout session')
      }

      const result = await response.json()
      
      // Redirect to Stripe Checkout immediately if URL exists
      if (result.subscription?.checkout_url) {
        window.location.href = result.subscription.checkout_url
        return result
      }
      
      // Only call onSuccess if we didn't redirect (completed subscription)
      onSuccess?.(result)
      return result

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
      onError?.(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  return {
    createSubscription,
    loading,
    error,
    clearError: () => setError(null)
  }
}
