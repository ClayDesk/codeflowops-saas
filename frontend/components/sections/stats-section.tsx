'use client'

import { TrendingUp, Users, Zap, Globe } from 'lucide-react'

const stats = [
  {
    icon: Zap,
    value: '2.5M+',
    label: 'Deployments per month',
    description: 'Successful deployments across all platforms',
    trend: '+15% this month'
  },
  {
    icon: Users,
    value: '500+',
    label: 'Enterprise customers',
    description: 'Fortune 500 companies trust our platform',
    trend: '+12% growth'
  },
  {
    icon: TrendingUp,
    value: '99.9%',
    label: 'Uptime guarantee',
    description: 'Industry-leading reliability and performance',
    trend: 'SLA maintained'
  },
  {
    icon: Globe,
    value: '40%',
    label: 'Average cost savings',
    description: 'Reduction in deployment costs and time',
    trend: 'Typical savings'
  }
]

export function StatsSection() {
  return (
    <section className="py-20 bg-primary/5">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-3xl font-bold text-foreground sm:text-4xl">
            Trusted by teams worldwide
          </h2>
          <p className="mt-4 text-lg text-muted-foreground">
            Join thousands of companies that have already transformed their deployment workflows
          </p>
        </div>

        {/* Stats grid */}
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-4">
          {stats.map((stat, index) => (
            <div 
              key={index}
              className="group relative rounded-2xl border border-border bg-background p-8 text-center hover:bg-muted/50 transition-all duration-300 hover:shadow-lg"
            >
              {/* Icon */}
              <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-lg bg-primary/10 group-hover:bg-primary/20 transition-colors mb-6">
                <stat.icon className="h-6 w-6 text-primary" />
              </div>
              
              {/* Value */}
              <div className="text-4xl font-bold text-foreground mb-2 lg:text-5xl">
                {stat.value}
              </div>
              
              {/* Label */}
              <div className="text-sm font-semibold text-foreground mb-3">
                {stat.label}
              </div>
              
              {/* Description */}
              <p className="text-sm text-muted-foreground mb-4">
                {stat.description}
              </p>
              
              {/* Trend */}
              <div className="inline-flex items-center rounded-full bg-green-50 px-3 py-1 text-xs font-medium text-green-700">
                {stat.trend}
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  )
}
