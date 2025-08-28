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
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
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
              <h1 className="text-3xl font-bold text-gray-900 mb-2">
                Complete Your Subscription
              </h1>
              <p className="text-gray-600">
                Start your 14-day free trial today. No credit card required.
              </p>
            </div>
            
            <StripeCheckout 
              onSuccess={() => {
                // Handle success - redirect to dashboard or success page
                console.log('Subscription successful!')
              }}
              onCancel={() => setShowCheckout(false)}
            />
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-purple-50">
      {/* Header */}
      <div className="container mx-auto px-4 py-16">
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4">
            <Star className="w-4 h-4 mr-1" />
            Most Popular
          </Badge>
          <h1 className="text-4xl md:text-6xl font-bold text-gray-900 mb-6">
            Simple, Transparent Pricing
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Start your deployment automation journey with a 14-day free trial. 
            No setup fees, no hidden costs.
          </p>
        </div>

        {/* Pricing Card */}
        <div className="max-w-md mx-auto">
          <Card className="relative overflow-hidden border-2 border-blue-200 shadow-xl">
            <div className="absolute top-0 left-0 right-0 h-2 bg-gradient-to-r from-blue-500 to-purple-600"></div>
            
            <CardHeader className="text-center pb-8 pt-8">
              <div className="mb-4">
                <Zap className="w-12 h-12 text-blue-500 mx-auto mb-4" />
              </div>
              <CardTitle className="text-2xl font-bold">CodeFlowOps Pro</CardTitle>
              <CardDescription className="text-gray-600 mt-2">
                Everything you need for professional deployment automation
              </CardDescription>
              
              <div className="mt-6">
                <div className="flex items-center justify-center">
                  <span className="text-5xl font-bold text-gray-900">$12</span>
                  <span className="text-gray-600 ml-2">/month</span>
                </div>
                <div className="flex items-center justify-center mt-2 text-sm text-green-600">
                  <Clock className="w-4 h-4 mr-1" />
                  14-day free trial
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6">
              {/* Features */}
              <div className="space-y-3">
                {features.map((feature, index) => (
                  <div key={index} className="flex items-center">
                    <CheckCircle className="w-5 h-5 text-green-500 mr-3 flex-shrink-0" />
                    <span className="text-gray-700">{feature}</span>
                  </div>
                ))}
              </div>

              {/* Security Badge */}
              <div className="border-t pt-6">
                <div className="flex items-center justify-center text-sm text-gray-600">
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
                  Start Free Trial
                </Button>
                <p className="text-xs text-gray-500 text-center mt-3">
                  Cancel anytime. No questions asked.
                </p>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Trust Indicators */}
        <div className="mt-16 text-center">
          <p className="text-gray-600 mb-8">Trusted by developers worldwide</p>
          <div className="flex justify-center items-center space-x-8 opacity-60">
            <div className="text-2xl font-bold text-gray-400">AWS</div>
            <div className="text-2xl font-bold text-gray-400">Azure</div>
            <div className="text-2xl font-bold text-gray-400">GCP</div>
            <div className="text-2xl font-bold text-gray-400">Docker</div>
          </div>
        </div>

        {/* FAQ Section */}
        <div className="mt-20 max-w-3xl mx-auto">
          <h2 className="text-3xl font-bold text-center mb-12">Frequently Asked Questions</h2>
          <div className="grid md:grid-cols-2 gap-8">
            <div>
              <h3 className="font-semibold mb-2">How does the free trial work?</h3>
              <p className="text-gray-600 text-sm">
                Get full access to all Pro features for 14 days. No credit card required to start.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Can I cancel anytime?</h3>
              <p className="text-gray-600 text-sm">
                Yes, you can cancel your subscription at any time with no questions asked.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">What payment methods do you accept?</h3>
              <p className="text-gray-600 text-sm">
                We accept all major credit cards and debit cards through Stripe.
              </p>
            </div>
            <div>
              <h3 className="font-semibold mb-2">Do you offer refunds?</h3>
              <p className="text-gray-600 text-sm">
                Yes, we offer a full refund within 30 days of your first payment.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
