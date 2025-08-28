'use client'

import { useRouter } from 'next/navigation'
import { ArrowRight, Github, Zap, Shield, Globe } from 'lucide-react'
import { ProductScreenshot } from '@/components/ui/ProductScreenshot'
import { useAuth } from '@/lib/auth-context'

export function Hero() {
  const router = useRouter();
  const { isAuthenticated, loading } = useAuth();

  const handleDeploy = () => {
    if (isAuthenticated) {
      router.push('/deploy');
    } else {
      router.push('/register');
    }
  };

  return (
    <section className="relative min-h-[80vh] flex items-center justify-center bg-gradient-to-br from-white via-gray-50 to-blue-50 dark:from-gray-950 dark:via-gray-900 dark:to-blue-950 overflow-hidden">
      {/* Animated background blobs */}
      <div className="absolute top-0 left-0 w-96 h-96 bg-gradient-to-br from-blue-400 to-purple-400 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob1" />
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full mix-blend-multiply filter blur-2xl opacity-20 animate-blob2" />

      <div className="relative w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-20 flex flex-col md:flex-row items-center gap-12">
        {/* Left: Text & CTA */}
        <div className="flex-1 text-center md:text-left">
          <div className="inline-flex items-center space-x-2 bg-white/80 dark:bg-gray-900/80 backdrop-blur-sm border border-gray-200 dark:border-gray-800 rounded-full py-2 px-6 mb-8 shadow-sm">
            <Zap className="w-4 h-4 text-blue-600" />
            <span className="text-sm font-medium text-gray-700 dark:text-gray-200">Deploy in Minutes, Not Hours</span>
          </div>
          <h1 className="text-4xl md:text-6xl lg:text-7xl font-extrabold text-gray-900 dark:text-white mb-6 leading-tight">
            <span className="block">Modern DevOps</span>
            <span className="block bg-gradient-to-r from-blue-600 to-purple-600 bg-clip-text text-transparent">Zero Hassle.</span>
          </h1>
          <p className="text-xl md:text-2xl text-gray-600 dark:text-gray-300 mb-10 max-w-2xl leading-relaxed">
            Deploy React apps and static sites to AWS S3 + CloudFront in minutes. <span className="font-semibold text-blue-600 dark:text-blue-400">No DevOps required.</span> Paste your GitHub repo and go live instantly.
          </p>
          <div className="max-w-xl mx-auto md:mx-0 mb-8">
            <div className="flex justify-center md:justify-start">
              <button
                onClick={handleDeploy}
                className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-12 py-5 text-xl font-semibold whitespace-nowrap flex items-center justify-center space-x-3 rounded-2xl transition-all hover:shadow-lg hover:from-blue-700 hover:to-purple-700 transform hover:scale-105"
              >
                <span>{isAuthenticated ? 'Deploy Now' : 'Start Free Trial'}</span>
                <ArrowRight className="w-6 h-6" />
              </button>
            </div>
            <p className="text-sm text-gray-500 dark:text-gray-400 mt-4 text-center md:text-left">
              No credit card required • Deploy up to 5 projects free
            </p>
          </div>
          <div className="flex flex-wrap gap-4 justify-center md:justify-start mt-6">
            <div className="flex items-center space-x-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 rounded-xl border border-gray-200 dark:border-gray-700">
              <Zap className="w-5 h-5 text-yellow-500" />
              <span className="font-semibold text-gray-700 dark:text-gray-200">5-Minute Deploy</span>
            </div>
            <div className="flex items-center space-x-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 rounded-xl border border-gray-200 dark:border-gray-700">
              <Shield className="w-5 h-5 text-green-500" />
              <span className="font-semibold text-gray-700 dark:text-gray-200">Enterprise Security</span>
            </div>
            <div className="flex items-center space-x-2 px-4 py-2 bg-white/70 dark:bg-gray-800/70 rounded-xl border border-gray-200 dark:border-gray-700">
              <Globe className="w-5 h-5 text-blue-500" />
              <span className="font-semibold text-gray-700 dark:text-gray-200">Global CDN</span>
            </div>
          </div>
        </div>
        {/* Right: Product Screenshot/Illustration */}
        <div className="flex-1 flex justify-center items-center">
          <ProductScreenshot />
        </div>
      </div>
    </section>
  );
}
