import { useState } from 'react'

interface UseStripePaymentOptions {
  onSuccess?: (result: any) => void
  onError?: (error: string) => void
}

interface CreateSubscriptionParams {
  planTier: string
  pricingContext?: Record<string, any>
  trialDays?: number
}

interface UpgradeSubscriptionParams {
  subscriptionId: string
  newPlanTier: string
  pricingContext?: Record<string, any>
}

export function useStripePayment({ onSuccess, onError }: UseStripePaymentOptions = {}) {
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const API_BASE = 'https://api.codeflowops.com'

  const getAuthHeaders = () => {
    const token = localStorage.getItem('codeflowops_access_token')
    return {
      'Content-Type': 'application/json',
      ...(token && { Authorization: `Bearer ${token}` })
    }
  }

  const createSubscription = async (params: CreateSubscriptionParams) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/payments/create-subscription`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          plan_tier: params.planTier,
          pricing_context: params.pricingContext || {},
          trial_days: params.trialDays
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to create subscription')
      }

      const result = await response.json()

      if (result.subscription.client_secret) {
        // Return client secret for frontend payment confirmation
        return {
          ...result,
          requires_payment: true,
          client_secret: result.subscription.client_secret
        }
      }

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

  const upgradeSubscription = async (params: UpgradeSubscriptionParams) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/payments/upgrade-subscription`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          subscription_id: params.subscriptionId,
          new_plan_tier: params.newPlanTier,
          pricing_context: params.pricingContext || {}
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to upgrade subscription')
      }

      const result = await response.json()
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

  const cancelSubscription = async (subscriptionId: string, atPeriodEnd = true) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/payments/cancel-subscription`, {
        method: 'POST',
        headers: getAuthHeaders(),
        body: JSON.stringify({
          subscription_id: subscriptionId,
          at_period_end: atPeriodEnd
        })
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to cancel subscription')
      }

      const result = await response.json()
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

  const getSubscriptionStatus = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/payments/user-subscription-status`, {
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to get subscription status')
      }

      const result = await response.json()
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

  const getPricingWithPaymentInfo = async (context: Record<string, any> = {}) => {
    try {
      setLoading(true)
      setError(null)

      const params = new URLSearchParams()
      const entries = Object.keys(context).map(key => [key, context[key]])
      entries.forEach(([key, value]) => {
        if (value) params.append(key, value.toString())
      })

      const response = await fetch(
        `${API_BASE}/api/v1/payments/pricing-with-payment-info?${params.toString()}`,
        { headers: getAuthHeaders() }
      )

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to get pricing information')
      }

      const result = await response.json()
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

  const getCustomerPortalUrl = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/payments/customer-portal`, {
        method: 'POST',
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to get customer portal URL')
      }

      const result = await response.json()
      return result.url

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'An error occurred'
      setError(errorMessage)
      onError?.(errorMessage)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const getBillingHistory = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`${API_BASE}/api/v1/payments/billing-history`, {
        headers: getAuthHeaders()
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.detail || 'Failed to get billing history')
      }

      const result = await response.json()
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
    loading,
    error,
    createSubscription,
    upgradeSubscription,
    cancelSubscription,
    getSubscriptionStatus,
    getPricingWithPaymentInfo,
    getCustomerPortalUrl,
    getBillingHistory,
    clearError: () => setError(null)
  }
}
