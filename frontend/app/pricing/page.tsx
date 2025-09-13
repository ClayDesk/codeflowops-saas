'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, Star, Zap, Shield, Clock } from 'lucide-react'
import { StripeCheckout } from '@/components/StripeCheckout'

export default function PricingPage() {
  const [showCheckout, setShowCheckout] = React.useState(false)

  const features = [
    "Unlimited repository analysis",
    "AI-powered deployment recommendations", 
    "Multi-cloud support (AWS, GCP, Azure)",
    "Custom deployment templates",
    "Real-time monitoring & alerts",
    "Priority support & assistance",
    "Advanced security scanning",
    "Team collaboration tools"
  ]

  if (showCheckout) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-950 dark:to-blue-950">
        <div className="container mx-auto px-4 py-16">
          <div className="max-w-2xl mx-auto">
            <div className="text-center mb-8">
              <Button 
                variant="ghost" 
                onClick={() => setShowCheckout(false)}
                className="mb-4"
              >
                ← Back to Pricing
              </Button>
              <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                Complete Your Subscription
              </h1>
              <p className="text-gray-600 dark:text-gray-300">
                Complete your subscription with immediate access. Secure payment processing.
              </p>
            </div>
            
            <StripeCheckout 
              onSuccess={() => {
                const frontendUrl = window.location.origin
                window.location.href = `${frontendUrl}/deploy?success=true&subscription=completed`
              }}
              onCancel={() => setShowCheckout(false)}
            />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50 dark:from-gray-900 dark:via-gray-950 dark:to-blue-950">
      {/* Header */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4">
            <Star className="w-4 h-4 mr-1" />
            Most Popular
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 dark:text-white mb-6">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Start your deployment automation journey with immediate access.
            No setup fees, no hidden costs.
          </p>
        </div>

        {/* Pricing Card */}
        <div className="max-w-md mx-auto">
          <Card className="relative overflow-hidden border-2 border-blue-200 dark:border-blue-800 shadow-xl dark:bg-gray-900">
            <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-500 to-purple-600"></div>
            
            <CardHeader className="text-center pb-8 pt-8">
              <div className="mb-4">
                <Zap className="w-12 h-12 text-blue-500 dark:text-blue-400 mx-auto mb-4" />
              </div>
              <CardTitle className="text-2xl font-bold dark:text-white">CodeFlowOps Pro</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-300 mt-2">
                Everything you need for professional deployment automation
              </CardDescription>
              
              <div className="mt-6">
                <div className="flex items-center justify-center">
                  <span className="text-5xl font-bold text-gray-900 dark:text-white">$19</span>
                  <span className="text-gray-600 dark:text-gray-300 ml-2">/month</span>
                </div>
                <div className="flex items-center justify-center mt-2 text-sm text-green-600 dark:text-green-400">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Immediate access
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6 dark:bg-gray-900">
              {/* Features */}
              <div className="space-y-3">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-center">
                    <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400 mr-3 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                  </div>
                ))}
              </div>

              {/* Security Badge */}
              <div className="border-t dark:border-gray-700 pt-6">
                <div className="flex items-center justify-center text-sm text-gray-600 dark:text-gray-300">
                  <Shield className="w-4 h-4 mr-2" />
                  <span>Enterprise-grade security & compliance</span>
                </div>
              </div>

              {/* CTA Button */}
              <div className="pt-4">
                <Button 
                  className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-3 text-lg"
                  onClick={() => setShowCheckout(true)}
                >
                  Get Started Now
                </Button>
                <p className="text-xs text-gray-500 dark:text-gray-400 text-center mt-3">
                  Secure payment. Cancel anytime.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Trust Indicators */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 dark:text-gray-300 mb-8">Trusted by developers worldwide</p>
          <div className="flex justify-center items-center space-x-8 opacity-60">
            <div className="text-2xl font-bold text-gray-400 dark:text-gray-500">AWS</div>
            <div className="text-2xl font-bold text-gray-400 dark:text-gray-500">Azure</div>
            <div className="text-2xl font-bold text-gray-400 dark:text-gray-500">GCP</div>
            <div className="text-2xl font-bold text-gray-400 dark:text-gray-500">Docker</div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-20 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12 dark:text-white">Frequently Asked Questions</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold mb-2 dark:text-white">How does the payment work?</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                Get immediate access to all Pro features. Secure payment processing with your credit card.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2 dark:text-white">Can I cancel anytime?</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                Yes, you can cancel your subscription at any time with no questions asked.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2 dark:text-white">What payment methods do you accept?</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                We accept all major credit cards and debit cards through Stripe.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2 dark:text-white">Do you offer refunds?</h3>
              <p className="text-gray-600 dark:text-gray-300 text-sm">
                Yes, we offer a full refund within 30 days of your first payment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
