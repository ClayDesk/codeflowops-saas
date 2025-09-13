'use client'

import { 
  Cloud, 
  GitBranch, 
  Shield, 
  Zap, 
  Globe, 
  BarChart3,
  Users,
  Lock,
  Workflow
} from 'lucide-react'

const features = [
  {
    icon: Cloud,
    title: 'Multi-Cloud Deployment',
    description: 'Deploy to AWS, Azure, GCP, and 20+ other cloud providers from a single platform.',
    benefits: ['Unified dashboard', 'Cost optimization', 'Vendor lock-in prevention']
  },
  {
    icon: GitBranch,
    title: 'Advanced CI/CD',
    description: 'Sophisticated pipelines with automated testing, security scanning, and rollback capabilities.',
    benefits: ['Zero-downtime deployments', 'Automated rollbacks', 'Security scanning']
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'SOC 2 compliant with end-to-end encryption, RBAC, and compliance reporting.',
    benefits: ['SOC 2 compliance', 'End-to-end encryption', 'Role-based access']
  },
  {
    icon: BarChart3,
    title: 'Real-time Analytics',
    description: 'Comprehensive monitoring and analytics with custom dashboards and alerting.',
    benefits: ['Custom dashboards', 'Real-time monitoring', 'Smart alerting']
  },
  {
    icon: Users,
    title: 'Team Collaboration',
    description: 'Built-in tools for team management, code reviews, and deployment approvals.',
    benefits: ['Team management', 'Code reviews', 'Approval workflows']
  },
  {
    icon: Workflow,
    title: 'Automation Engine',
    description: 'AI-powered automation that learns from your patterns and optimizes workflows.',
    benefits: ['AI optimization', 'Pattern learning', 'Workflow automation']
  }
]

export function FeaturesSection() {
  return (
    <section className="py-20 bg-muted/30">
      <div className="mx-auto max-w-7xl px-6 lg:px-8">
        {/* Section header */}
        <div className="text-center max-w-3xl mx-auto mb-16">
          <h2 className="text-4xl font-bold text-foreground sm:text-5xl">
            Everything you need to
            <span className="text-gradient-brand"> scale your deployments</span>
          </h2>
          <p className="mt-6 text-lg text-muted-foreground">
            From development to production, our platform provides all the tools and features 
            your team needs to deploy with confidence and scale without limits.
          </p>
        </div>

        {/* Features grid */}
        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature, index) => (
            <div 
              key={index}
              className="group relative rounded-2xl border border-border bg-background p-8 hover:bg-muted/50 transition-all duration-300 hover:shadow-lg hover:border-primary/20"
            >
              {/* Icon */}
              <div className="flex h-14 w-14 items-center justify-center rounded-xl bg-primary/10 group-hover:bg-primary/20 transition-colors">
                <feature.icon className="h-7 w-7 text-primary" />
              </div>
              
              {/* Content */}
              <h3 className="mt-6 text-xl font-semibold text-foreground">
                {feature.title}
              </h3>
              <p className="mt-3 text-muted-foreground leading-relaxed">
                {feature.description}
              </p>
              
              {/* Benefits list */}
              <ul className="mt-6 space-y-2">
                {feature.benefits.map((benefit, benefitIndex) => (
                  <li key={benefitIndex} className="flex items-center text-sm">
                    <div className="h-1.5 w-1.5 rounded-full bg-primary mr-3" />
                    <span className="text-muted-foreground">{benefit}</span>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>

        {/* CTA section */}
        <div className="mt-16 text-center">
          <div className="rounded-2xl border border-border bg-card p-8 md:p-12">
            <h3 className="text-2xl font-bold text-foreground mb-4">
              Ready to transform your deployment workflow?
            </h3>
            <p className="text-muted-foreground mb-8 max-w-2xl mx-auto">
              Join thousands of teams already using CodeFlowOps to deploy faster, scale better, and worry less.
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
              <button className="btn-primary">
                <Zap className="mr-2 h-5 w-5" />
                Get Started
              </button>
              <button className="btn-outline">
                Schedule demo
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
