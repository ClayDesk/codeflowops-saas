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
  return (
    <section id="features" className="py-20 bg-gray-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <span className="inline-block bg-blue-100 text-blue-700 px-3 py-1 rounded-full text-sm font-medium mb-4">Two Powerful Services</span>
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 mb-6">
            Deploy React Apps & Static Sites to AWS in Minutes
          </h2>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Choose the perfect deployment solution for your project. From complex React applications to simple static websites, we've got you covered.
          </p>
        </div>

        {/* Main Services */}
        <div className="grid md:grid-cols-2 gap-8 mb-20">
          {mainServices.map((service, index) => (
            <div key={index} className="bg-white p-8 rounded-2xl shadow-sm border border-gray-100 hover:shadow-lg transition-shadow">
              <div className={`inline-flex p-3 rounded-2xl ${service.bgColor} mb-6`}>
                <service.icon className={`w-6 h-6 ${service.color}`} />
              </div>
              <h3 className="text-2xl font-bold text-gray-900 mb-4">{service.title}</h3>
              <p className="text-gray-600 mb-6">{service.description}</p>
              <div className="grid grid-cols-2 gap-3">
                {service.features.map((feature, featureIndex) => (
                  <div key={featureIndex} className="flex items-center text-sm text-gray-600">
                    <div className="w-1.5 h-1.5 bg-blue-500 rounded-full mr-2"></div>
                    {feature}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>

        {/* Additional Features */}
        <div className="text-center mb-12">
          <h3 className="text-2xl font-bold text-gray-900 mb-4">Enterprise-Grade Features for Both Services</h3>
          <p className="text-gray-600">Every deployment includes these powerful features</p>
        </div>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div key={index} className="bg-white p-6 rounded-2xl hover:shadow-md transition-shadow">
              <div className={`inline-flex p-3 rounded-xl ${feature.bgColor} mb-4`}>
                <feature.icon className={`w-5 h-5 ${feature.color}`} />
              </div>
              <h3 className="font-semibold text-gray-900 mb-2">{feature.title}</h3>
              <p className="text-sm text-gray-600">{feature.description}</p>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold text-white mb-4">
              Ready to Deploy Your First Project?
            </h3>
            <p className="text-blue-100 mb-6">
              Join thousands of developers who have streamlined their deployment workflow
            </p>
            <button className="bg-white text-blue-600 px-8 py-3 rounded-xl font-semibold hover:bg-gray-50 transition-colors">
              Start Free Trial
            </button>
          </div>
        </div>
      </div>
    </section>
  )
}
