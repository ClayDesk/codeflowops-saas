'use client'

import { useState, useEffect } from 'react'
import { useDynamicPricing } from '@/hooks/use-dynamic-pricing'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, XCircle, Loader2, Gift, Info } from 'lucide-react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { QuickCheckoutButton } from '@/components/stripe/StripeCheckout'

interface SubscriptionPricingProps {
  currentPlan?: string
}

export function SubscriptionPricing({ currentPlan = 'free' }: SubscriptionPricingProps) {
  const { pricing, loading, error, formatPrice } = useDynamicPricing()
  const [showFallback, setShowFallback] = useState(false)

  // Add timeout fallback for subscription page
  useEffect(() => {
    const timer = setTimeout(() => {
      if (loading && !pricing) {
        setShowFallback(true)
      }
    }, 5000) // 5 second timeout

    return () => clearTimeout(timer)
  }, [loading, pricing])

  // Show fallback if loading too long or on error
  if ((loading && !showFallback) && !error) {
    return (
      <div className="text-center py-12">
        <Loader2 className="h-8 w-8 animate-spin mx-auto text-blue-600" />
        <p className="text-gray-600 dark:text-gray-300 mt-2">Loading subscription options...</p>
      </div>
    )
  }

  // Fallback pricing if dynamic pricing fails
  const fallbackPlans = [
    {
      tier: 'free',
      name: 'Free',
      price_monthly: 0,
      description: 'Perfect for personal projects',
      features: ['3 projects', 'Public repositories', 'Basic AWS infrastructure', 'Standard build times', 'Community support'],
      max_projects: 3,
      popular: false
    },
    {
      tier: 'starter',
      name: 'Starter',
      price_monthly: 1900,
      description: 'Great for freelancers and small teams',
      features: ['10 projects', 'Private repositories', 'Custom domains with SSL', 'Fast build times', 'Email support', 'API access'],
      max_projects: 10,
      popular: true,
      trial_days: 14
    },
    {
      tier: 'pro',
      name: 'Pro',
      price_monthly: 4900,
      description: 'For professional teams with advanced needs',
      features: ['Unlimited projects', 'Priority support', 'Advanced analytics', 'Team collaboration (10 members)', 'Deployment previews'],
      max_projects: -1,
      popular: false,
      trial_days: 7
    },
    {
      tier: 'enterprise',
      name: 'Enterprise',
      price_monthly: 0,
      description: 'For large teams and organizations',
      features: ['Everything in Pro', 'Unlimited team members', 'White-label solution', 'Dedicated support', 'Custom integrations'],
      max_projects: -1,
      popular: false
    }
  ]

  const plans = pricing?.plans || fallbackPlans

  const getPlanButton = (plan: any) => {
    const isCurrentPlan = currentPlan === plan.tier
    const cta = plan.tier === 'free' ? 'Get Started Free' :
                plan.tier === 'enterprise' ? 'Contact Sales' :
                plan.trial_days && plan.trial_days > 0 ? `Start ${plan.trial_days}-Day Trial` :
                'Get Started'

    if (isCurrentPlan) {
      return (
        <Button 
          variant="secondary"
          className="w-full"
          disabled
        >
          Current Plan
        </Button>
      )
    }

    if (plan.tier === 'free') {
      return (
        <Button 
          variant="outline"
          className="w-full"
          onClick={() => window.location.href = '/register?plan=free'}
        >
          {cta}
        </Button>
      )
    }

    if (plan.tier === 'enterprise') {
      return (
        <Button 
          variant="default"
          className="w-full"
          onClick={() => window.location.href = '/contact?plan=enterprise'}
        >
          {cta}
        </Button>
      )
    }

    // For paid plans, use Stripe checkout
    return (
      <QuickCheckoutButton
        planTier={plan.tier}
        planName={plan.name}
        planPrice={formatPrice(plan.promotional_price || plan.price_monthly)}
        planFeatures={plan.features}
        trialDays={plan.trial_days}
        pricingContext={{ source: 'profile_page', current_plan: currentPlan }}
      >
        {cta}
      </QuickCheckoutButton>
    )
  }

  return (
    <div className="space-y-6">
      {/* Dynamic pricing insights */}
      {pricing && pricing.personalization && pricing.personalization.applied && pricing.personalization.applied.length > 0 && (
        <Alert className="bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800">
          <Gift className="h-4 w-4 text-green-600" />
          <AlertDescription className="text-green-800 dark:text-green-200">
            <strong>Special pricing applied:</strong> {pricing.personalization.applied.map(p => p.description).join(', ')}
          </AlertDescription>
        </Alert>
      )}

      {/* Error state */}
      {error && (
        <Alert className="bg-yellow-50 dark:bg-yellow-900/20 border-yellow-200 dark:border-yellow-800">
          <Info className="h-4 w-4 text-yellow-600" />
          <AlertDescription className="text-yellow-800 dark:text-yellow-200">
            Unable to load personalized pricing. Showing standard rates.
          </AlertDescription>
        </Alert>
      )}

      {/* Pricing Plans Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {plans.map((plan) => {
          const isCurrentPlan = currentPlan === plan.tier
          const isPopular = plan.popular
          const displayPrice = (plan as any).promotional_price || plan.price_monthly
          const hasDiscount = (plan as any).promotional_price && (plan as any).promotional_price < plan.price_monthly

          return (
            <div
              key={plan.tier}
              className={`border rounded-lg p-6 space-y-4 relative ${
                isPopular ? 'border-2 border-blue-500' : 'border'
              } ${isCurrentPlan ? 'bg-gray-50 dark:bg-gray-800' : ''}`}
            >
              {/* Popular Badge */}
              {isPopular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-blue-500">Most Popular</Badge>
                </div>
              )}

              {/* Discount badges */}
              {hasDiscount && (
                <div className="absolute -top-2 -right-2">
                  <Badge variant="destructive" className="text-xs">Sale</Badge>
                </div>
              )}

              <div>
                <h3 className="text-lg font-semibold">{plan.name}</h3>
                <div className="flex items-baseline">
                  <p className="text-2xl font-bold">
                    {plan.tier === 'enterprise' ? 'Custom' : formatPrice(displayPrice)}
                  </p>
                  {plan.tier !== 'enterprise' && plan.tier !== 'free' && (
                    <span className="text-sm font-normal">/per month</span>
                  )}
                </div>
                
                {/* Original price if discounted */}
                {hasDiscount && (
                  <p className="text-sm text-gray-400 line-through">
                    {formatPrice(plan.price_monthly)}
                  </p>
                )}

                {/* Trial information */}
                {plan.trial_days && plan.trial_days > 0 && (
                  <Badge variant="outline" className="text-xs mt-1">
                    {plan.trial_days} days free trial
                  </Badge>
                )}

                <p className="text-sm text-muted-foreground mt-2">{plan.description}</p>
              </div>

              <ul className="space-y-2 text-sm">
                {plan.features.map((feature: string, index: number) => (
                  <li key={index} className="flex items-center gap-2">
                    <CheckCircle className="h-4 w-4 text-green-500" />
                    {feature}
                  </li>
                ))}
              </ul>

              {getPlanButton(plan)}
            </div>
          )
        })}
      </div>

      {/* Recommendations */}
      {pricing?.recommendations && (
        <div className="mt-6 max-w-2xl mx-auto">
          <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
            <div className="flex items-center text-blue-800 dark:text-blue-200">
              <Info className="h-5 w-5 mr-2" />
              <div>
                <p className="font-medium">Recommended for you: {pricing.recommendations.recommended_plan.toUpperCase()}</p>
                <p className="text-sm">{pricing.recommendations.reason}</p>
                {pricing.recommendations.savings_opportunity && (
                  <p className="text-sm mt-1">
                    💰 {pricing.recommendations.savings_opportunity.description} - 
                    Save {pricing.recommendations.savings_opportunity.savings_amount}
                  </p>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
