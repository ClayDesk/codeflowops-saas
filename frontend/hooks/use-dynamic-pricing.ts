import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'

interface PricingPlan {
  id: string
  name: string
  tier: string
  price_monthly: number
  price_yearly: number
  max_projects: number
  max_team_members: number
  features: string[]
  description: string
  popular: boolean
  trial_days: number
  promotional_price?: number
  first_time_discount?: number
  student_discount?: number
  holiday_discount?: number
  geographic_discount?: boolean
  trial_description?: string
  promotion_name?: string
  promotion_expires?: string
}

interface PricingResponse {
  plans: PricingPlan[]
  currency: string
  personalization: {
    applied: Array<{
      type: string
      description: string
    }>
    user_segment: string
  }
  recommendations: {
    recommended_plan: string
    reason: string
    savings_opportunity?: {
      type: string
      description: string
      savings_amount: string
    }
  }
}

interface UseDynamicPricingOptions {
  country?: string
  currency?: string
  referralCode?: string
  companySize?: string
  abVariant?: string
}

export function useDynamicPricing(options: UseDynamicPricingOptions = {}) {
  const [pricing, setPricing] = useState<PricingResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const { user, isAuthenticated } = useAuth()

  useEffect(() => {
    fetchDynamicPricing()
  }, [options, isAuthenticated])

  const fetchDynamicPricing = async () => {
    try {
      setLoading(true)
      setError(null)

      // Build query parameters
      const params = new URLSearchParams()
      
      if (options.country) params.append('country', options.country)
      if (options.currency) params.append('currency', options.currency)
      if (options.referralCode) params.append('referral_code', options.referralCode)
      if (options.companySize) params.append('company_size', options.companySize)
      if (options.abVariant) params.append('ab_variant', options.abVariant)

      // Auto-detect country if not provided
      if (!options.country) {
        try {
          const geoResponse = await fetch('https://ipapi.co/json/')
          const geoData = await geoResponse.json()
          if (geoData.country_code) {
            params.append('country', geoData.country_code)
          }
        } catch (geoError) {
          console.warn('Could not detect country:', geoError)
        }
      }

      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
      const url = `${API_BASE}/api/v1/pricing${params.toString() ? '?' + params.toString() : ''}`

      const headers: HeadersInit = {
        'Content-Type': 'application/json',
      }

      // Add auth header if user is authenticated
      if (isAuthenticated) {
        const token = localStorage.getItem('codeflowops_access_token')
        if (token) {
          headers.Authorization = `Bearer ${token}`
        }
      }

      const response = await fetch(url, { headers })

      if (!response.ok) {
        throw new Error(`Failed to fetch pricing: ${response.statusText}`)
      }

      const data: PricingResponse = await response.json()
      
      // Process pricing data
      const processedData = {
        ...data,
        plans: data.plans.map(plan => ({
          ...plan,
          features: typeof plan.features === 'string' 
            ? JSON.parse(plan.features) 
            : plan.features,
          // Calculate display price (promotional or regular)
          displayPrice: plan.promotional_price || plan.price_monthly,
          hasDiscount: Boolean(plan.promotional_price && plan.promotional_price < plan.price_monthly),
          discountPercentage: plan.promotional_price 
            ? Math.round((1 - plan.promotional_price / plan.price_monthly) * 100)
            : 0
        }))
      }

      setPricing(processedData)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch pricing'
      setError(errorMessage)
      console.error('Dynamic pricing error:', err)

      // Fallback to static pricing
      setPricing(getFallbackPricing())

    } finally {
      setLoading(false)
    }
  }

  const getFallbackPricing = (): PricingResponse => {
    return {
      plans: [
        {
          id: 'plan_free',
          name: 'Free',
          tier: 'free',
          price_monthly: 0,
          price_yearly: 0,
          max_projects: 3,
          max_team_members: 1,
          features: ['3 projects', 'Public repositories', 'Community support'],
          description: 'Perfect for personal projects',
          popular: false,
          trial_days: 0
        },
        {
          id: 'plan_starter',
          name: 'Starter',
          tier: 'starter',
          price_monthly: 1900,
          price_yearly: 19000,
          max_projects: 10,
          max_team_members: 3,
          features: ['10 projects', 'Private repositories', 'Email support'],
          description: 'Great for small teams',
          popular: true,
          trial_days: 14
        },
        {
          id: 'plan_pro',
          name: 'Pro',
          tier: 'pro',
          price_monthly: 4900,
          price_yearly: 49000,
          max_projects: -1,
          max_team_members: 10,
          features: ['Unlimited projects', 'Priority support', 'Advanced analytics'],
          description: 'For professional teams',
          popular: false,
          trial_days: 7
        },
        {
          id: 'plan_enterprise',
          name: 'Enterprise',
          tier: 'enterprise',
          price_monthly: 0,
          price_yearly: 0,
          max_projects: -1,
          max_team_members: -1,
          features: ['Everything in Pro', 'Custom integrations', 'Dedicated support'],
          description: 'For large organizations',
          popular: false,
          trial_days: 0
        }
      ],
      currency: 'USD',
      personalization: {
        applied: [],
        user_segment: 'general'
      },
      recommendations: {
        recommended_plan: 'starter',
        reason: 'Most popular choice'
      }
    }
  }

  const formatPrice = (priceInCents: number, currency: string = 'USD') => {
    if (priceInCents === 0) return 'Free'
    
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: currency,
      minimumFractionDigits: 0
    }).format(priceInCents / 100)
  }

  const getRecommendedPlan = () => {
    if (!pricing) return null
    return pricing.plans.find(plan => plan.tier === pricing.recommendations.recommended_plan)
  }

  const getPopularPlan = () => {
    if (!pricing) return null
    return pricing.plans.find(plan => plan.popular)
  }

  return {
    pricing,
    loading,
    error,
    formatPrice,
    getRecommendedPlan,
    getPopularPlan,
    refetch: fetchDynamicPricing
  }
}
