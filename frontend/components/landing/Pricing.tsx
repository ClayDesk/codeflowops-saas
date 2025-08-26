'use client'

import Link from 'next/link'
import { Check, Star } from 'lucide-react'
import { Badge } from '@/components/ui/badge'

// Define the plan interface for type safety
interface PlanDisplay {
  name: string
  price: string
  originalPrice?: string | null
  period: string
  description: string
  features: string[]
  notIncluded: string[]
  cta: string
  popular: boolean
  href: string
  discounts?: {
    promotional?: boolean
    student?: boolean
    geographic?: boolean
    holiday?: boolean
  }
  maxProjects?: number | string
  maxTeamMembers?: number | string
  trialDays?: number
}

// Fallback static plans (same as before for when dynamic pricing fails)
const fallbackPlans: PlanDisplay[] = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Perfect for personal projects and learning',
    features: [
      '3 projects',
      'Public repositories',
      'Basic AWS infrastructure',
      'Standard build times',
      'Community support'
    ],
    notIncluded: [
      'Private repositories',
      'Custom domains',
      'Priority support',
      'Advanced analytics'
    ],
    cta: 'Get Started Free',
    popular: false,
    href: '/register?plan=free',
    trialDays: 0
  },
  {
    name: 'Starter',
    price: '$19',
    period: 'per month',
    description: 'Great for freelancers and small teams',
    features: [
      '10 projects',
      'Private repositories',
      'Custom domains with SSL',
      'Fast build times',
      'Email support',
      'API access',
      'Environment variables'
    ],
    notIncluded: [
      'Priority support',
      'Advanced analytics',
      'Team collaboration'
    ],
    cta: 'Start 14-Day Trial',
    popular: true,
    href: '/register?plan=starter',
    trialDays: 14
  },
  {
    name: 'Pro',
    price: '$49',
    period: 'per month',
    description: 'For professional teams with advanced needs',
    features: [
      'Unlimited projects',
      'Private repositories',
      'Custom domains with SSL',
      'Priority support',
      'Advanced analytics',
      'Team collaboration (10 members)',
      'Deployment previews',
      'GitHub integration'
    ],
    notIncluded: [
      'White-label options',
      'Dedicated support',
      'Custom integrations'
    ],
    cta: 'Start Pro Trial',
    popular: false,
    href: '/register?plan=pro',
    trialDays: 7
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'contact us',
    description: 'For large teams and organizations',
    features: [
      'Everything in Pro',
      'Unlimited team members',
      'White-label solution',
      'Dedicated support manager',
      'Custom integrations & APIs',
      'SLA guarantees (99.9% uptime)',
      'Advanced security & compliance',
      'Custom workflows & automation',
      'Multi-region deployments'
    ],
    notIncluded: [],
    cta: 'Contact Sales',
    popular: false,
    href: '/contact?plan=enterprise',
    trialDays: 0
  }
]

interface PricingProps {
  hideFreePlan?: boolean
}

export function Pricing({ hideFreePlan = false }: PricingProps) {
  // Use static pricing for landing page - no API calls needed
  const plans = fallbackPlans
  const filteredPlans = hideFreePlan ? plans.filter(plan => plan.name !== 'Free') : plans

  return (
    <section id="pricing" className="py-20 bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-950">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-block bg-blue-100 dark:bg-blue-900 text-blue-700 dark:text-blue-300 px-3 py-1 rounded-full text-sm font-medium mb-4">
            Simple Pricing
          </span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-6">
            Deploy React & Static Sites at Any Scale
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Choose the plan that fits your needs. Both services included in all plans.
            No hidden fees, no surprises.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className={`grid grid-cols-1 ${filteredPlans.length === 3 ? 'md:grid-cols-3' : 'md:grid-cols-2 lg:grid-cols-4'} gap-8 max-w-7xl mx-auto`}>
          {filteredPlans.map((plan, index) => (
            <div
              key={index}
              className={`relative bg-white dark:bg-gray-800 p-8 rounded-2xl border border-gray-200 dark:border-gray-700 transition-all duration-200 hover:shadow-lg ${
                plan.popular
                  ? 'ring-2 ring-blue-500 dark:ring-blue-400 shadow-lg transform scale-105'
                  : 'hover:ring-1 hover:ring-gray-200'
              }`}
            >
              {/* Popular badge */}
              {plan.popular && (
                <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                  <div className="bg-blue-600 text-white px-3 py-1 rounded-full text-sm font-medium flex items-center">
                    <Star className="w-4 h-4 mr-1" />
                    Most Popular
                  </div>
                </div>
              )}

              {/* Discount badges */}
              {plan.discounts && (
                <div className="absolute -top-2 -right-2 space-y-1">
                  {plan.discounts.promotional && (
                    <Badge variant="destructive" className="text-xs">Sale</Badge>
                  )}
                  {plan.discounts.student && (
                    <Badge variant="secondary" className="text-xs">Student</Badge>
                  )}
                  {plan.discounts.geographic && (
                    <Badge variant="outline" className="text-xs">Regional</Badge>
                  )}
                </div>
              )}

              <div className="text-center mb-8">
                <div className="mb-4">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-white mb-2">
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline justify-center">
                    <span className="text-4xl font-bold text-gray-900 dark:text-white">
                      {plan.price}
                    </span>
                    {plan.period !== 'contact us' && (
                      <span className="text-gray-500 dark:text-gray-400 ml-1">/{plan.period}</span>
                    )}
                  </div>
                  {plan.originalPrice && plan.originalPrice !== plan.price && (
                    <div className="mt-1">
                      <span className="text-lg text-gray-400 line-through">{plan.originalPrice}</span>
                    </div>
                  )}
                  {plan.trialDays && plan.trialDays > 0 && (
                    <div className="mt-2">
                      <Badge variant="outline" className="text-xs">
                        {plan.trialDays} days free trial
                      </Badge>
                    </div>
                  )}
                </div>
                <p className="text-gray-600 dark:text-gray-300">{plan.description}</p>
              </div>

              {/* Features */}
              <div className="space-y-4 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-start">
                    <Check className="w-5 h-5 text-green-500 dark:text-green-400 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-600 dark:text-gray-300 ml-3">{feature}</span>
                  </div>
                ))}
                
                {/* Not included features (for fallback) */}
                {plan.notIncluded && plan.notIncluded.length > 0 && plan.notIncluded.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-start opacity-50">
                    <div className="w-5 h-5 mt-0.5 flex-shrink-0">
                      <div className="w-4 h-4 border-2 border-gray-300 dark:border-gray-600 rounded ml-0.5 mt-0.5"></div>
                    </div>
                    <span className="text-gray-400 dark:text-gray-500 line-through ml-3">{feature}</span>
                  </div>
                ))}
              </div>

              {/* CTA Button */}
              <Link
                href={plan.href}
                className={`block w-full text-center py-3 px-6 rounded-xl font-semibold transition-all ${
                  plan.popular
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : plan.name === 'Free'
                    ? 'bg-gray-100 dark:bg-gray-700 text-gray-900 dark:text-white hover:bg-gray-200 dark:hover:bg-gray-600'
                    : 'bg-blue-600 text-white hover:bg-blue-700'
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>

        {/* Bottom section */}
        <div className="mt-20 text-center">
          <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">
            Frequently Asked Questions
          </h3>
          <div className="grid md:grid-cols-2 gap-8 text-left">
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Can I change plans anytime?</h4>
              <p className="text-gray-600 dark:text-gray-300">Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Do you offer refunds?</h4>
              <p className="text-gray-600 dark:text-gray-300">We offer a 30-day money-back guarantee for all paid plans, no questions asked.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">What payment methods do you accept?</h4>
              <p className="text-gray-600 dark:text-gray-300">We accept all major credit cards, PayPal, and wire transfers for enterprise customers.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 dark:text-white mb-2">Is there a free trial?</h4>
              <p className="text-gray-600 dark:text-gray-300">Yes! Most paid plans include free trials. No credit card required to start.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
