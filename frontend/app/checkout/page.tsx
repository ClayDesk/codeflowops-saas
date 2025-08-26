import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Checkout | CodeFlowOps',
  description: 'Complete your subscription to CodeFlowOps',
}

export default function CheckoutPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-50 to-white dark:from-gray-900 dark:to-gray-950 py-12">
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Complete Your Subscription
          </h1>
          <p className="text-xl text-gray-600 dark:text-gray-400">
            Choose your plan and get started with CodeFlowOps today
          </p>
        </div>
        
        <div className="bg-white dark:bg-gray-800 rounded-2xl shadow-lg p-8">
          <div className="text-center">
            <h2 className="text-2xl font-semibold text-gray-900 dark:text-white mb-4">
              Checkout Coming Soon
            </h2>
            <p className="text-gray-600 dark:text-gray-300 mb-8">
              We&apos;re finalizing our secure checkout process. In the meantime, you can register for a free account and we&apos;ll notify you when paid plans are available.
            </p>
            <div className="space-y-4">
              <a
                href="/register"
                className="inline-block bg-blue-600 text-white px-8 py-3 rounded-xl font-semibold hover:bg-blue-700 transition-colors"
              >
                Register for Free Account
              </a>
              <div>
                <a
                  href="/contact"
                  className="text-blue-600 dark:text-blue-400 hover:underline"
                >
                  Contact us for enterprise pricing
                </a>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
