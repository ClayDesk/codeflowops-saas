'use client'

import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle } from 'lucide-react'

interface SubscriptionPricingProps {
  currentPlan?: string
}

export function SubscriptionPricing({ currentPlan = 'free' }: SubscriptionPricingProps) {
  // Use static pricing for reliability - no API calls, no loading states
  const formatPrice = (priceInCents: number) => {
    if (priceInCents === 0) return 'Free'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(priceInCents / 100)
  }

  const staticPlans = [
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
          variant="outline"
          className="w-full"
          onClick={() => window.location.href = '/contact?plan=enterprise'}
        >
          {cta}
        </Button>
      )
    }

    return (
      <Button 
        className="w-full"
        onClick={() => window.location.href = `/register?plan=${plan.tier}`}
      >
        {cta}
      </Button>
    )
  }

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {staticPlans.map((plan) => {
          const isCurrentPlan = currentPlan === plan.tier
          const displayPrice = plan.price_monthly

          return (
            <div
              key={plan.tier}
              className={`relative p-6 rounded-lg border transition-all duration-200 ${
                plan.popular
                  ? 'border-blue-500 ring-1 ring-blue-500 shadow-lg'
                  : isCurrentPlan
                  ? 'border-green-500 ring-1 ring-green-500'
                  : 'border-gray-200 dark:border-gray-700'
              }`}
            >
              {/* Popular Badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <Badge className="bg-blue-600 text-white">Most Popular</Badge>
                </div>
              )}

              {/* Current Plan Badge */}
              {isCurrentPlan && (
                <div className="absolute -top-3 right-4">
                  <Badge variant="secondary" className="bg-green-600 text-white">Current Plan</Badge>
                </div>
              )}

              <div className="text-center mb-6">
                <h3 className="text-lg font-semibold mb-2">{plan.name}</h3>
                <div className="mb-2">
                  <span className="text-3xl font-bold">
                    {plan.tier === 'enterprise' ? 'Custom' : formatPrice(displayPrice)}
                  </span>
                  {plan.tier !== 'free' && plan.tier !== 'enterprise' && (
                    <span className="text-gray-500 dark:text-gray-400">/month</span>
                  )}
                </div>
                <p className="text-sm text-gray-600 dark:text-gray-400">{plan.description}</p>
              </div>

              {/* Features */}
              <div className="space-y-3 mb-6">
                {plan.features.map((feature, index) => (
                  <div key={index} className="flex items-start">
                    <CheckCircle className="h-5 w-5 text-green-500 mt-0.5 mr-3 flex-shrink-0" />
                    <span className="text-sm">{feature}</span>
                  </div>
                ))}
              </div>

              {/* CTA Button */}
              {getPlanButton(plan)}
            </div>
          )
        })}
      </div>
    </div>
  )
}
