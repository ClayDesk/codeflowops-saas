'use client'

import { Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { StripeCheckout } from '@/components/StripeCheckout'
import { Loader2 } from 'lucide-react'

function CheckoutContent() {
  const searchParams = useSearchParams()
  const clientSecret = searchParams.get('client_secret')
  const planTier = searchParams.get('plan') || 'starter'
  
  // Plan configurations
  const planConfigs: Record<string, any> = {
    starter: {
      name: 'Starter',
      price: '$19',
      features: ['10 projects', 'Private repositories', 'Custom domains', 'Email support'],
      trialDays: 0
    },
    pro: {
      name: 'Pro', 
      price: '$49',
      features: ['Unlimited projects', 'Priority support', 'Advanced analytics', 'Team collaboration'],
      trialDays: 0
    },
    enterprise: {
      name: 'Enterprise',
      price: 'Custom',
      features: ['Everything in Pro', 'Unlimited team members', 'White-label solution', 'Dedicated support'],
      trialDays: 0
    }
  }
  
  const currentPlan = planConfigs[planTier as keyof typeof planConfigs] || planConfigs.starter

  // If no client_secret but we have a plan, use StripeCheckout to create the session
  if (!clientSecret && planTier) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-950 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          {/* Back Button */}
          <div className="mb-8">
            <a
              href="/pricing"
              className="inline-flex items-center text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 font-medium"
            >
              ← Back to Pricing
            </a>
          </div>
          
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Complete Your Subscription
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              Subscribe to {currentPlan.name} for {currentPlan.price}/month
              <span className="block text-blue-600 dark:text-blue-400 font-semibold">
                Payment will be processed immediately
              </span>
            </p>
          </div>
          
          <div className="max-w-2xl mx-auto">
            <StripeCheckout
              onSuccess={() => {
                const frontendUrl = window.location.origin
                window.location.href = `${frontendUrl}/deploy?success=true&subscription=completed`
              }}
              onCancel={() => {
                const frontendUrl = window.location.origin
                window.location.href = `${frontendUrl}/#pricing`
              }}
            />
          </div>
        </div>
      </div>
    )
  }

  if (!clientSecret) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-950 py-12">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-12">
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
              Checkout
            </h1>
            <p className="text-xl text-gray-600 dark:text-gray-400">
              No payment session found. Please return to pricing to select a plan.
            </p>
          </div>
          
          <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
            <div className="text-center">
              <div className="space-y-4">
                <a
                  href="/profile?tab=subscription"
                  className="inline-block bg-blue-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
                >
                  Return to Pricing
                </a>
                <div>
                  <a
                    href="/contact"
                    className="text-blue-600 dark:text-blue-400 hover:underline"
                  >
                    Contact us for help
                  </a>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-950 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Complete Your Subscription
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Subscribe to {currentPlan.name} for {currentPlan.price}/month
          </p>
        </div>
        
        <div className="max-w-2xl mx-auto">
          <StripeCheckout
            onSuccess={() => {
              window.location.href = '/profile?tab=subscription&success=true'
            }}
            onCancel={() => {
              window.location.href = '/profile?tab=subscription'
            }}
          />
        </div>
      </div>
    </div>
  )
}

export default function CheckoutPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center">
        <Loader2 className="h-8 w-8 animate-spin" />
      </div>
    }>
      <CheckoutContent />
    </Suspense>
  )
}
