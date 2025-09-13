'use client'

import { Star, Quote } from 'lucide-react'
import { useRouter } from 'next/navigation'

const testimonials = [
  {
    name: 'Sarah Chen',
    role: 'Frontend Developer',
    company: 'TechCorp',
    avatar: 'https://ui-avatars.com/api/?name=Sarah+Chen&background=3b82f6&color=ffffff&size=64',
    content: 'CodeFlowOps saved me hours of DevOps work. I can now deploy my React apps in minutes instead of struggling with AWS configurations for hours.',
    rating: 5
  },
  {
    name: 'Marcus Johnson',
    role: 'Full Stack Engineer',
    company: 'StartupXYZ',
    avatar: 'https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?w=64&h=64&fit=crop&crop=face',
    content: 'The automated deployment pipeline is incredible. Push to GitHub and boom - my app is live on AWS with CloudFront. Perfect for our startup pace.',
    rating: 5
  },
  {
    name: 'Emily Rodriguez',
    role: 'Tech Lead',
    company: 'DigitalFirst',
    avatar: 'https://images.unsplash.com/photo-1438761681033-6461ffad8d80?w=64&h=64&fit=crop&crop=face',
    content: 'We migrated our entire deployment process to CodeFlowOps. The team productivity increased by 40% and we eliminated deployment-related downtime.',
    rating: 5
  },
  {
    name: 'David Kim',
    role: 'Senior Developer',
    company: 'WebSolutions',
    avatar: 'https://images.unsplash.com/photo-1507003211169-0a1dd7228f2d?w=64&h=64&fit=crop&crop=face',
    content: 'As someone who dreaded AWS setup, CodeFlowOps is a game-changer. The intelligent project detection works flawlessly with our React and Vue projects.',
    rating: 5
  },
  {
    name: 'Lisa Thompson',
    role: 'Product Manager',
    company: 'InnovateCo',
    avatar: 'https://images.unsplash.com/photo-1487412720507-e7ab37603c6f?w=64&h=64&fit=crop&crop=face',
    content: 'The deployment speed is phenomenal. Our stakeholders can see feature updates live within minutes of approval. It has revolutionized our development cycle.',
    rating: 5
  },
  {
    name: 'James Wilson',
    role: 'Freelance Developer',
    company: 'Independent',
    avatar: 'https://images.unsplash.com/photo-1500648767791-00dcc994a43e?w=64&h=64&fit=crop&crop=face',
    content: 'CodeFlowOps lets me focus on coding instead of deployment headaches. My clients love how quickly I can show them progress. Worth every penny!',
    rating: 5
  }
]

export function Testimonials() {
  const router = useRouter()

  return (
    <section id="testimonials" className="py-20 bg-white dark:bg-gray-900">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="text-center mb-16">
          <h2 className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-4">
            Loved by developers worldwide
          </h2>
          <p className="text-xl text-gray-600 dark:text-gray-300 max-w-3xl mx-auto">
            Join thousands of developers who have transformed their deployment workflow with CodeFlowOps.
          </p>
        </div>

        {/* Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8 mb-16">
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-2">10K+</div>
            <div className="text-gray-600 dark:text-gray-400">Deployments</div>
          </div>
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-2">2K+</div>
            <div className="text-gray-600 dark:text-gray-400">Happy Developers</div>
          </div>
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-2">99.9%</div>
            <div className="text-gray-600 dark:text-gray-400">Uptime</div>
          </div>
          <div className="text-center">
            <div className="text-3xl md:text-4xl font-bold text-gray-900 dark:text-white mb-2">4.9/5</div>
            <div className="text-gray-600 dark:text-gray-400">Rating</div>
          </div>
        </div>

        {/* Testimonials Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
          {testimonials.map((testimonial, index) => (
            <div
              key={index}
              className="bg-gray-50 dark:bg-gray-800 rounded-xl p-6 hover:bg-gray-100 dark:hover:bg-gray-700 transition-colors duration-200 border border-gray-100 dark:border-gray-700"
            >
              {/* Quote icon */}
              <Quote className="w-8 h-8 text-blue-500 dark:text-blue-400 mb-4" />
              
              {/* Rating */}
              <div className="flex items-center mb-4">
                {[...Array(testimonial.rating)].map((_, i) => (
                  <Star
                    key={i}
                    className="w-4 h-4 text-yellow-400 fill-current"
                  />
                ))}
              </div>

              {/* Content */}
              <p className="text-gray-700 dark:text-gray-300 mb-6 leading-relaxed">
                "{testimonial.content}"
              </p>

              {/* Author */}
              <div className="flex items-center">
                <img
                  src={testimonial.avatar}
                  alt={testimonial.name}
                  className="w-12 h-12 rounded-full mr-4"
                />
                <div>
                  <div className="font-semibold text-gray-900 dark:text-white">
                    {testimonial.name}
                  </div>
                  <div className="text-gray-600 dark:text-gray-400 text-sm">
                    {testimonial.role} at {testimonial.company}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* Bottom CTA */}
        <div className="mt-16 text-center">
          <div className="bg-gradient-to-r from-blue-600 to-purple-600 rounded-2xl p-8 text-white">
            <h3 className="text-2xl font-bold mb-4">
              Join thousands of satisfied developers
            </h3>
            <p className="text-blue-100 mb-6 max-w-2xl mx-auto">
              Start your deployment journey today and see why developers love CodeFlowOps.
            </p>
            <div className="flex justify-center">
              <button 
                onClick={() => router.push('/pricing')}
                className="bg-white text-blue-600 px-8 py-3 rounded-lg font-semibold hover:bg-blue-50 transition-colors"
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </div>
    </section>
  )
}
