'use client'

import React from 'react'
import { useRouter } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { CheckCircle, Star, Zap, Clock, ArrowRight } from 'lucide-react'

export function Pricing() {
  const router = useRouter()

  const freeFeatures = [
    "Up to 5 projects",
    "Basic deployment automation",
    "GitHub integration",
    "Standard templates",
    "Community support"
  ]

  const proFeatures = [
    "Unlimited projects",
    "AI-powered recommendations", 
    "Multi-cloud support",
    "Custom templates",
    "Real-time monitoring",
    "Priority support",
    "Advanced security",
    "Team collaboration"
  ]

  return (
    <section id="pricing" className="py-24 bg-gradient-to-br from-gray-50 to-blue-50 dark:from-gray-900 dark:to-gray-800">
      <div className="container mx-auto px-4">
        <div className="text-center mb-16">
          <Badge variant="secondary" className="mb-4 dark:bg-gray-700 dark:text-gray-300">
            <Star className="w-4 h-4 mr-1" />
            Transparent Pricing
          </Badge>
          <h2 className="text-4xl md:text-5xl font-bold text-gray-900 dark:text-white mb-6">
            Start Free, Scale When Ready
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Deploy your first projects for free. Upgrade to Pro when you need advanced features and unlimited deployments.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-5xl mx-auto">
          {/* Free Plan */}
          <Card className="relative border-2 border-gray-200 dark:border-gray-700 shadow-lg hover:shadow-xl transition-shadow dark:bg-gray-800">
            <CardHeader className="text-center pb-8">
              <div className="mb-4">
                <Zap className="w-10 h-10 text-gray-600 dark:text-gray-400 mx-auto" />
              </div>
              <CardTitle className="text-2xl font-bold dark:text-white">Free Starter</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-300 mt-2">
                Perfect for personal projects and getting started
              </CardDescription>
              
              <div className="mt-6">
                <div className="flex items-center justify-center">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">$0</span>
                  <span className="text-gray-600 dark:text-gray-300 ml-2">/month</span>
                </div>
                <div className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                  Forever free
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6 dark:bg-gray-800">
              <ul className="space-y-3">
                {freeFeatures.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-green-500 dark:text-green-400 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>

              <Button 
                className="w-full bg-gray-600 hover:bg-gray-700 dark:bg-gray-600 dark:hover:bg-gray-500 text-white py-3"
                onClick={() => router.push('/deploy')}
              >
                Start Building Free
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>
            </CardContent>
          </Card>

          {/* Pro Plan */}
          <Card className="relative border-2 border-blue-500 dark:border-blue-400 shadow-xl hover:shadow-2xl transition-shadow dark:bg-gray-800">
            <div className="absolute top-0 left-0 right-0 h-1 bg-gradient-to-r from-blue-500 to-purple-600"></div>
            <Badge className="absolute -top-3 left-1/2 transform -translate-x-1/2 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
              Most Popular
            </Badge>
            
            <CardHeader className="text-center pb-8 pt-8">
              <div className="mb-4">
                <Zap className="w-10 h-10 text-blue-500 dark:text-blue-400 mx-auto" />
              </div>
              <CardTitle className="text-2xl font-bold dark:text-white">CodeFlowOps Pro</CardTitle>
              <CardDescription className="text-gray-600 dark:text-gray-300 mt-2">
                For teams and professional projects
              </CardDescription>
              
              <div className="mt-6">
                <div className="flex items-center justify-center">
                  <span className="text-4xl font-bold text-gray-900 dark:text-white">$19</span>
                  <span className="text-gray-600 dark:text-gray-300 ml-2">/month</span>
                </div>
                <div className="flex items-center justify-center mt-2 text-sm text-green-600 dark:text-green-400">
                  <CheckCircle className="w-4 h-4 mr-1" />
                  Immediate access
                </div>
              </div>
            </CardHeader>

            <CardContent className="space-y-6 dark:bg-gray-800">
              <ul className="space-y-3">
                {proFeatures.map((feature, index) => (
                  <li key={index} className="flex items-start">
                    <CheckCircle className="w-5 h-5 text-blue-500 dark:text-blue-400 mr-3 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-700 dark:text-gray-300">{feature}</span>
                  </li>
                ))}
              </ul>

              <Button
                className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white py-3 font-semibold"
                onClick={() => router.push('/pricing')}
              >
                Get Started Now
                <ArrowRight className="w-4 h-4 ml-2" />
              </Button>

              <div className="text-center text-xs text-gray-500 dark:text-gray-400">
                Secure payment • Cancel anytime
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Trust indicators */}
        <div className="text-center mt-16">
          <p className="text-sm text-gray-500 dark:text-gray-400 mb-4">Trusted by developers worldwide</p>
          <div className="flex justify-center items-center space-x-6 text-gray-400 dark:text-gray-500">
            <span className="text-sm">🔒 SSL Secured</span>
            <span className="text-sm">💳 Stripe Payments</span>
            <span className="text-sm">⚡ Instant Setup</span>
            <span className="text-sm">🌍 Global CDN</span>
          </div>
        </div>
      </div>
    </section>
  )
}

export default Pricing
