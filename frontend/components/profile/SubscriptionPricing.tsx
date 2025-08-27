'use client'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { useStripePayment } from '@/hooks/use-stripe-payment'
import { useState } from 'react'
import { Loader2 } from 'lucide-react'

interface Plan {
  tier: string
  name: string
  price_monthly: number
  description: string
  features: string[]
  max_projects: number
  popular?: boolean
  trial_days?: number
}

interface SubscriptionPricingProps {
  currentPlan?: string
}

export function SubscriptionPricing({ currentPlan = 'free' }: SubscriptionPricingProps) {
  const [loadingPlan, setLoadingPlan] = useState<string | null>(null)
  
  const { createSubscription } = useStripePayment({
    onSuccess: (result) => {
      if (result.checkout_url) {
        window.location.href = result.checkout_url
      }
    },
    onError: (error) => {
      console.error('Subscription creation failed:', error)
      setLoadingPlan(null)
    }
  })
  const formatPrice = (priceInCents: number) => {
    if (priceInCents === 0) return 'Free'
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0
    }).format(priceInCents / 100)
  }

  const staticPlans: Plan[] = [
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

  const getPlanButton = (plan: Plan) => {
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
          disabled={true}
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

    const handleSubscribe = async () => {
      setLoadingPlan(plan.tier)
      await createSubscription({
        planTier: plan.tier,
        trialDays: plan.trial_days
      })
    }

    return (
      <Button 
        className="w-full"
        onClick={handleSubscribe}
        disabled={loadingPlan === plan.tier}
      >
        {loadingPlan === plan.tier ? (
          <>
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            Creating...
          </>
        ) : (
          cta
        )}
      </Button>
    )
  }

  return (
    <div className="py-8">
      <div className="text-center mb-12">
        <h2 className="text-3xl font-bold mb-4">Choose Your Plan</h2>
        <p className="text-lg text-muted-foreground">
          Scale your development workflow with our flexible pricing
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {staticPlans.map((plan) => (
          <Card 
            key={plan.tier} 
            className={`relative ${
              plan.popular 
                ? 'border-primary shadow-lg scale-105' 
                : ''
            }`}
          >
            {plan.popular && (
              <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                <span className="bg-primary text-primary-foreground px-3 py-1 rounded-full text-sm font-medium">
                  Most Popular
                </span>
              </div>
            )}
            
            <CardHeader className="text-center">
              <CardTitle className="text-xl mb-2">{plan.name}</CardTitle>
              <div className="mb-4">
                <span className="text-4xl font-bold">
                  {formatPrice(plan.price_monthly)}
                </span>
                {plan.price_monthly > 0 && (
                  <span className="text-muted-foreground">/month</span>
                )}
              </div>
              <CardDescription>{plan.description}</CardDescription>
            </CardHeader>
            
            <CardContent className="space-y-4">
              <ul className="space-y-2 mb-6">
                {plan.features.map((feature, index) => (
                  <li key={index} className="flex items-center text-sm">
                    <span className="mr-2 text-primary">✓</span>
                    {feature}
                  </li>
                ))}
              </ul>
              
              {getPlanButton(plan)}
              
              {plan.trial_days && plan.trial_days > 0 && (
                <p className="text-xs text-center text-muted-foreground">
                  {plan.trial_days}-day free trial • Cancel anytime
                </p>
              )}
            </CardContent>
          </Card>
        ))}
      </div>
      
      <div className="mt-12 text-center">
        <p className="text-sm text-muted-foreground">
          All plans include our core deployment features. 
          <br />
          Need something custom? <a href="/contact" className="text-primary hover:underline">Contact us</a>
        </p>
      </div>
    </div>
  )
}
