'use client'

import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { ArrowRight } from 'lucide-react'
import { useAuth } from '@/lib/auth-context'

export function CTASection() {
  const { isAuthenticated, loading } = useAuth()

  return (
    <section className="py-16 bg-primary/5">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        <div className="text-center">
          <h2 className="text-3xl font-bold text-foreground">Ready to get started?</h2>
          <p className="mt-4 text-muted-foreground">
            Join thousands of developers who trust CodeFlowOps for their deployment needs.
          </p>
          <div className="mt-8 flex flex-col sm:flex-row items-center justify-center gap-4">
            {isAuthenticated ? (
              <Link href="/deploy">
                <Button size="lg">
                  Deploy Your App Now
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            ) : (
              <Link href="/register">
                <Button size="lg">
                  Get Started
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
            )}
            {!isAuthenticated && (
              <Link href="/login">
                <Button size="lg" variant="outline">
                  Sign In
                </Button>
              </Link>
            )}
          </div>
        </div>
      </div>
    </section>
  )
}
