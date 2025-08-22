import { Check, Star, ArrowRight } from 'lucide-react'

const plans = [
  {
    name: 'Free',
    price: '$0',
    period: 'forever',
    description: 'Perfect for personal projects and learning',
    features: [
      '5 React/Static deployments per month',
      'Public repositories only',
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
    href: '/register?plan=free'
  },
  {
    name: 'Pro',
    price: '$9',
    period: 'per month',
    description: 'Best for professional developers and small teams',
    features: [
      'Unlimited React & Static deployments',
      'Private repositories',
      'Custom domains with SSL',
      'Fast build times',
      'Email support',
      'Advanced analytics',
      'Environment variables',
      'Deployment previews',
      'GitHub integration',
      'CloudFront CDN'
    ],
    notIncluded: [
      'White-label options',
      'Dedicated support',
      'Custom integrations'
    ],
    cta: 'Start Pro Trial',
    popular: true,
    href: '/register?plan=pro'
  },
  {
    name: 'Enterprise',
    price: 'Custom',
    period: 'contact us',
    description: 'For large teams and organizations',
    features: [
      'Everything in Pro',
      'White-label solution',
      'Dedicated support manager',
      'Custom integrations & APIs',
      'SLA guarantees (99.9% uptime)',
      'Advanced security & compliance',
      'Team management & permissions',
      'Priority builds & deployment',
      'Custom workflows & automation',
      'Multi-region deployments'
    ],
    notIncluded: [],
    cta: 'Contact Sales',
    popular: false,
    href: '/contact?plan=enterprise'
  }
]

export function Pricing() {
  return (
    <section id="pricing" className="py-20 bg-gradient-to-br from-gray-50 to-white">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium mb-4">Simple Pricing</span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
            Deploy React & Static Sites at Any Scale
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Choose the plan that fits your needs. Both services included in all plans.
            No hidden fees, no surprises.
          </p>
        </div>

        {/* Pricing Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-5xl mx-auto">
          {plans.map((plan, index) => (
            <div
              key={index}
              className={`relative bg-white p-8 rounded-2xl border transition-all duration-200 hover:shadow-lg ${
                plan.popular
                  ? 'ring-2 ring-blue-500 shadow-lg transform scale-105'
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

              <div className="text-center mb-8">
                <div className="mb-4">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">
                    {plan.name}
                  </h3>
                  <div className="flex items-baseline justify-center">
                    <span className="text-4xl font-bold text-gray-900">
                      {plan.price}
                    </span>
                    {plan.period !== 'contact us' && (
                      <span className="text-gray-500 ml-1">/{plan.period}</span>
                    )}
                  </div>
                </div>
                <p className="text-gray-600">{plan.description}</p>
              </div>

              {/* Features */}
              <div className="space-y-4 mb-8">
                {plan.features.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-start">
                    <Check className="w-5 h-5 text-green-500 mt-0.5 flex-shrink-0" />
                    <span className="text-gray-600 ml-3">{feature}</span>
                  </div>
                ))}
                
                {/* Not included features */}
                {plan.notIncluded.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-start opacity-50">
                    <div className="w-5 h-5 mt-0.5 flex-shrink-0">
                      <div className="w-4 h-4 border-2 border-gray-300 rounded ml-0.5 mt-0.5"></div>
                    </div>
                    <span className="text-gray-400 line-through ml-3">{feature}</span>
                  </div>
                ))}
              </div>

              {/* CTA Button */}
              <a
                href={plan.href}
                className={`block w-full text-center py-3 px-6 rounded-xl font-semibold transition-all ${
                  plan.popular
                    ? 'bg-blue-600 text-white hover:bg-blue-700'
                    : 'bg-gray-100 text-gray-900 hover:bg-gray-200'
                }`}
              >
                {plan.cta}
              </a>
            </div>
          ))}
        </div>

        {/* Bottom section */}
        <div className="mt-20 text-center">
          <h3 className="text-2xl font-bold text-gray-900 mb-8">
            Frequently Asked Questions
          </h3>
          <div className="grid md:grid-cols-2 gap-8 text-left">
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Can I change plans anytime?</h4>
              <p className="text-gray-600">Yes! You can upgrade or downgrade your plan at any time. Changes take effect immediately.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Do you offer refunds?</h4>
              <p className="text-gray-600">We offer a 30-day money-back guarantee for all paid plans, no questions asked.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">What payment methods do you accept?</h4>
              <p className="text-gray-600">We accept all major credit cards, PayPal, and wire transfers for enterprise customers.</p>
            </div>
            <div>
              <h4 className="font-semibold text-gray-900 mb-2">Is there a free trial?</h4>
              <p className="text-gray-600">Yes! Pro plan includes a 14-day free trial. No credit card required to start.</p>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
