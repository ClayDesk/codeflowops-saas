'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  ArrowRight, 
  Play, 
  Zap, 
  Shield, 
  Globe,
  CheckCircle,
  Star
} from 'lucide-react'

const stats = [
  { label: 'Deployments per month', value: '2.5M+' },
  { label: 'Enterprise customers', value: '500+' },
  { label: 'Uptime guarantee', value: '99.9%' },
  { label: 'Cost savings average', value: '40%' },
]

const trustedByLogos = [
  { name: 'TechCorp', logo: '/logos/techcorp.svg' },
  { name: 'InnovateLabs', logo: '/logos/innovatelabs.svg' },
  { name: 'GlobalSystems', logo: '/logos/globalsystems.svg' },
  { name: 'FutureWorks', logo: '/logos/futureworks.svg' },
  { name: 'DataDriven', logo: '/logos/datadriven.svg' },
]

const benefits = [
  'Deploy to 20+ cloud providers',
  'Zero-downtime deployments',
  'Enterprise-grade security',
  'Cost optimization built-in'
]

export function HeroSection() {
  const [isVideoPlaying, setIsVideoPlaying] = useState(false)

  return (
    <section className="relative overflow-hidden bg-background">
      {/* Background gradient */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-background to-secondary/5" />
      
      {/* Hero content */}
      <div className="relative mx-auto max-w-7xl px-6 py-16 sm:py-24 lg:px-8 lg:py-32">
        {/* Badge */}
        <div className="mb-8 flex justify-center lg:justify-start">
          <div className="relative rounded-full px-3 py-1 text-sm leading-6 text-muted-foreground ring-1 ring-border hover:ring-primary/50 transition-colors">
            <span className="absolute inset-0 rounded-full bg-gradient-to-r from-primary/10 to-secondary/10" />
            <span className="relative flex items-center gap-2">
              <Star className="h-4 w-4 text-primary" fill="currentColor" />
              New: AI-powered deployment optimization
              <ArrowRight className="h-4 w-4" />
            </span>
          </div>
        </div>

        <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 lg:gap-16 items-center">
          {/* Left column - Main content */}
          <div className="text-center lg:text-left">
            {/* Main headline */}
            <h1 className="text-5xl font-bold tracking-tight text-foreground sm:text-6xl lg:text-7xl xl:text-8xl">
              <span className="block">Deploy</span>
              <span className="block text-gradient-brand">Everywhere</span>
              <span className="block">Effortlessly</span>
            </h1>

            {/* Subheadline */}
            <p className="mt-8 text-lg leading-8 text-muted-foreground sm:text-xl lg:text-2xl max-w-2xl lg:max-w-none">
              Transform your development workflow with intelligent automation, 
              multi-tenant deployment orchestration, and enterprise-grade DevOps tools.
            </p>
            
            <p className="mt-4 text-xl font-semibold text-foreground">
              Deploy faster, scale better, worry less.
            </p>

            {/* Benefits list */}
            <div className="mt-8 flex flex-wrap justify-center lg:justify-start gap-3">
              {benefits.map((benefit, index) => (
                <div key={index} className="flex items-center gap-2 rounded-full bg-primary/10 px-4 py-2">
                  <CheckCircle className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium text-foreground">{benefit}</span>
                </div>
              ))}
            </div>

            {/* CTA buttons */}
            <div className="mt-10 flex flex-col sm:flex-row items-center justify-center lg:justify-start gap-4">
              <Link href="/deploy">
                <Button size="lg" className="w-full sm:w-auto text-base px-8 py-6">
                  <Zap className="mr-2 h-5 w-5" />
                  Deploy Now
                  <ArrowRight className="ml-2 h-5 w-5" />
                </Button>
              </Link>
              
              <Link href="/auth/signup">
                <Button size="lg" variant="outline" className="w-full sm:w-auto text-base px-8 py-6">
                  Start free trial
                </Button>
              </Link>
              
              <button
                onClick={() => setIsVideoPlaying(true)}
                className="w-full sm:w-auto inline-flex items-center gap-3 rounded-lg border border-border bg-background px-8 py-6 text-base font-medium text-foreground hover:bg-muted transition-colors"
              >
                <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary/10">
                  <Play className="h-5 w-5 text-primary fill-primary" />
                </div>
                Watch demo
              </button>
            </div>
          </div>

          {/* Right column - Visual/Stats */}
          <div className="relative">
            {/* Feature highlights in a card layout */}
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-1 xl:grid-cols-2">
              <div className="rounded-xl border border-border bg-card p-6 hover:bg-muted/50 transition-colors">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 mb-4">
                  <Zap className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Lightning Fast
                </h3>
                <p className="text-sm text-muted-foreground">
                  Deploy in seconds, not hours. Our optimized pipeline ensures rapid delivery.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-6 hover:bg-muted/50 transition-colors">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 mb-4">
                  <Shield className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Enterprise Security
                </h3>
                <p className="text-sm text-muted-foreground">
                  Bank-grade security with SOC 2 compliance and end-to-end encryption.
                </p>
              </div>

              <div className="rounded-xl border border-border bg-card p-6 hover:bg-muted/50 transition-colors sm:col-span-2 lg:col-span-1 xl:col-span-2">
                <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 mb-4">
                  <Globe className="h-6 w-6 text-primary" />
                </div>
                <h3 className="text-lg font-semibold text-foreground mb-2">
                  Global Scale
                </h3>
                <p className="text-sm text-muted-foreground">
                  Deploy across 20+ cloud providers worldwide with intelligent routing.
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* Stats section - now more spread out */}
        <div className="mt-20 pt-12 border-t border-border">
          <div className="grid grid-cols-2 gap-8 md:grid-cols-4">
            {stats.map((stat, index) => (
              <div key={index} className="text-center">
                <div className="text-3xl font-bold text-foreground sm:text-4xl lg:text-5xl">
                  {stat.value}
                </div>
                <div className="mt-2 text-sm text-muted-foreground font-medium">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Trust indicators */}
        <div className="mt-16 text-center">
          <p className="text-sm font-medium text-muted-foreground mb-6">
            Trusted by industry leaders
          </p>
          <div className="flex flex-wrap items-center justify-center gap-8 opacity-60">
            {trustedByLogos.map((company) => (
              <div key={company.name} className="flex items-center justify-center px-4 py-2 rounded-lg bg-muted/30">
                <span className="text-sm font-semibold text-muted-foreground">
                  {company.name}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Video modal */}
      {isVideoPlaying && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/80 backdrop-blur-sm">
          <div className="relative w-full max-w-4xl mx-4">
            <button
              onClick={() => setIsVideoPlaying(false)}
              className="absolute -top-12 right-0 text-foreground hover:text-primary transition-colors"
            >
              <span className="sr-only">Close video</span>
              <svg className="h-8 w-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
            <div className="aspect-video rounded-lg bg-muted overflow-hidden">
              <div className="flex h-full items-center justify-center">
                <p className="text-muted-foreground">Demo video coming soon...</p>
              </div>
            </div>
          </div>
        </div>
      )}
    </section>
  )
}
