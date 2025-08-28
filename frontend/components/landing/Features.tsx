'use client'

import Link from 'next/link'
import { 
  Zap, 
  Shield, 
  Globe, 
  GitBranch, 
  Server, 
  MonitorSpeaker,
  Gauge,
  Lock,
  RefreshCw,
  Code,
  FileText
} from 'lucide-react'
import { useAuth } from '@/lib/auth-context'

const mainServices = [
  {
    icon: Code,
    title: 'React App Deployment',
    description: 'Deploy Next.js, Create React App, Vite, and any React-based applications with intelligent build detection and optimization.',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    features: ['Next.js Support', 'Vite Builds', 'Auto Dependencies', 'Build Optimization']
  },
  {
    icon: FileText,
    title: 'Static Site Hosting',
    description: 'Host HTML, CSS, JavaScript sites, Jekyll, Hugo, and any static site generator with instant global distribution.',
    color: 'text-purple-600',
    bgColor: 'bg-purple-50',
    features: ['Jekyll Support', 'Hugo Builds', 'Custom Domains', 'SSL Certificates']
  }
]

const features = [
  {
    icon: Zap,
    title: 'Lightning Fast Deployment',
    description: 'Deploy your applications in under 5 minutes with our optimized build pipeline and intelligent caching.',
    color: 'text-yellow-500',
    bgColor: 'bg-yellow-50'
  },
  {
    icon: Shield,
    title: 'Enterprise Security',
    description: 'Bank-grade security with AWS IAM, encrypted deployments, and SOC2 compliance.',
    color: 'text-green-500',
    bgColor: 'bg-green-50'
  },
  {
    icon: Globe,
    title: 'Global CDN',
    description: 'Instant worldwide distribution via CloudFront with 200+ edge locations for blazing fast loading.',
    color: 'text-blue-500',
    bgColor: 'bg-blue-50'
  },
  {
    icon: GitBranch,
    title: 'Git Integration',
    description: 'Seamless GitHub integration with automatic deployments on push and pull request previews.',
    color: 'text-purple-500',
    bgColor: 'bg-purple-50'
  },
  {
    icon: Gauge,
    title: 'Performance Optimized',
    description: 'Built-in performance optimizations including compression, caching, and asset optimization.',
    color: 'text-red-500',
    bgColor: 'bg-red-50'
  },
  {
    icon: Lock,
    title: 'SSL & Security',
    description: 'Automatic SSL certificates, security headers, and protection against common web vulnerabilities.',
    color: 'text-cyan-500',
    bgColor: 'bg-cyan-50'
  },
  {
    icon: RefreshCw,
    title: 'Zero Downtime',
    description: 'Blue-green deployments ensure your site stays online during updates with instant rollbacks.',
    color: 'text-orange-500',
    bgColor: 'bg-orange-50'
  },
  {
    icon: MonitorSpeaker,
    title: 'Real-time Monitoring',
    description: 'Comprehensive analytics, error tracking, and performance monitoring with detailed insights.',
    color: 'text-pink-500',
    bgColor: 'bg-pink-50'
  }
]

export function Features() {
  const { isAuthenticated } = useAuth()

  return (
    <section id="features" className="py-24 bg-gray-50 dark:bg-gray-950 transition-colors">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-20">
          <span className="inline-block bg-gradient-to-r from-blue-100 to-purple-100 dark:from-blue-900 dark:to-purple-900 text-blue-700 dark:text-blue-200 px-4 py-1 rounded-full text-base font-semibold mb-5 tracking-wide shadow-sm">Enterprise-Ready Cloud Deployment</span>
          <h2 className="text-4xl md:text-5xl font-extrabold text-gray-900 dark:text-white mb-6 leading-tight">
            All-in-One Platform for <span className="bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">React & Static Sites</span>
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Effortlessly deploy, secure, and scale your web projects with our robust, automated platform. Built for teams, trusted by professionals.
          </p>
        </div>

        {/* Main Services */}
        <div className="grid md:grid-cols-2 gap-10 mb-24">
          {mainServices.map((service, index) => (
            <div key={index} className="bg-white dark:bg-gray-900 p-10 rounded-3xl shadow-lg border border-gray-100 dark:border-gray-800 hover:shadow-2xl transition-shadow flex flex-col h-full">
              <div className={`inline-flex p-4 rounded-2xl ${service.bgColor} dark:bg-opacity-20 mb-6`}> 
                <service.icon className={`w-8 h-8 ${service.color}`} />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 dark:text-white mb-3">{service.title}</h3>
              <p className="text-gray-600 dark:text-gray-300 mb-6">{service.description}</p>
              <div className="grid grid-cols-2 gap-3 mt-auto">
                {service.features.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-center text-base text-gray-700 dark:text-gray-200">
                    <div className="w-2 h-2 bg-blue-500 rounded-full mr-2"></div>
                    {feature}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Additional Features */}
        <div className="text-center mb-14">
          <h3 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">Everything You Need for Modern Deployments</h3>
          <p className="text-lg text-gray-600 dark:text-gray-300">All plans include these advanced features</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="bg-white dark:bg-gray-900 p-7 rounded-2xl hover:shadow-xl border border-gray-100 dark:border-gray-800 transition-shadow flex flex-col items-center text-center">
              <div className={`inline-flex p-4 rounded-xl ${feature.bgColor} dark:bg-opacity-20 mb-4`}>
                <feature.icon className={`w-7 h-7 ${feature.color}`} />
              </div>
              <h3 className="font-semibold text-lg text-gray-900 dark:text-white mb-2">{feature.title}</h3>
              <p className="text-base text-gray-600 dark:text-gray-300">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-24 text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-3xl p-10 text-white shadow-xl inline-block">
            <h3 className="text-3xl font-bold text-white mb-3">
              Ready to Deploy Your First Project?
            </h3>
            <p className="text-blue-100 mb-6 text-lg">
              Join thousands of developers who have streamlined their deployment workflow
            </p>
            <Link href={isAuthenticated ? "/deploy" : "/register"}>
              <button className="bg-white text-blue-600 px-10 py-4 rounded-xl font-semibold text-lg hover:bg-gray-50 transition-colors">
                {isAuthenticated ? 'Deploy Now' : 'Start Free Trial'}
              </button>
            </Link>
          </div>
        </div>
      </div>
    </section>
  );
}
