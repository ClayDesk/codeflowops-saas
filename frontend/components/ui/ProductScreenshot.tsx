'use client'

import { Github, CheckCircle, ArrowRight, Settings, Globe } from 'lucide-react'

export function ProductScreenshot() {
  return (
    <div className="relative w-full max-w-md mx-auto">
      {/* Browser Chrome */}
      <div className="bg-gray-200 dark:bg-gray-700 rounded-t-xl p-3 flex items-center space-x-2">
        <div className="flex space-x-2">
          <div className="w-3 h-3 bg-red-400 rounded-full"></div>
          <div className="w-3 h-3 bg-yellow-400 rounded-full"></div>
          <div className="w-3 h-3 bg-green-400 rounded-full"></div>
        </div>
        <div className="flex-1 bg-white dark:bg-gray-600 rounded-md px-3 py-1 text-xs text-gray-600 dark:text-gray-300">
          app.codeflowops.com/deploy
        </div>
      </div>
      
      {/* App Interface */}
      <div className="bg-white dark:bg-gray-900 border-2 border-t-0 border-gray-200 dark:border-gray-700 rounded-b-xl p-6 shadow-xl">
        {/* Header */}
        <div className="text-center mb-6">
          <h2 className="text-xl font-bold text-gray-900 dark:text-white mb-2">Deploy Your App</h2>
          <p className="text-sm text-gray-600 dark:text-gray-300">Transform your GitHub repo into a live AWS deployment</p>
        </div>
        
        {/* Progress Steps */}
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center">
            <div className="w-8 h-8 bg-blue-600 text-white rounded-full flex items-center justify-center text-sm font-bold">
              1
            </div>
            <span className="ml-2 text-sm font-medium text-blue-600">Repository</span>
          </div>
          <div className="flex-1 h-0.5 bg-gray-300 dark:bg-gray-600 mx-2"></div>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400 rounded-full flex items-center justify-center text-sm">
              2
            </div>
            <span className="ml-2 text-sm text-gray-400">AWS Setup</span>
          </div>
          <div className="flex-1 h-0.5 bg-gray-300 dark:bg-gray-600 mx-2"></div>
          <div className="flex items-center">
            <div className="w-8 h-8 bg-gray-300 dark:bg-gray-600 text-gray-600 dark:text-gray-400 rounded-full flex items-center justify-center text-sm">
              3
            </div>
            <span className="ml-2 text-sm text-gray-400">Deploy</span>
          </div>
        </div>
        
        {/* Repository Input */}
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
              GitHub Repository URL
            </label>
            <div className="relative">
              <Github className="absolute left-3 top-1/2 transform -translate-y-1/2 w-4 h-4 text-gray-400" />
              <input
                type="text"
                value="https://github.com/user/my-react-app"
                readOnly
                className="w-full pl-10 pr-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-gray-50 dark:bg-gray-800 text-gray-900 dark:text-gray-100 text-sm"
              />
            </div>
          </div>
          
          {/* Analysis Result */}
          <div className="bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg p-4">
            <div className="flex items-center space-x-3">
              <CheckCircle className="w-5 h-5 text-green-600 dark:text-green-400" />
              <div className="flex-1">
                <p className="text-sm font-medium text-green-800 dark:text-green-200">
                  Repository Analyzed Successfully
                </p>
                <p className="text-xs text-green-600 dark:text-green-300">
                  Detected: React.js • Build: npm run build • Deploy: S3 + CloudFront
                </p>
              </div>
              <div className="bg-blue-100 dark:bg-blue-900 text-blue-800 dark:text-blue-200 px-2 py-1 rounded text-xs font-medium">
                ⚛️ React
              </div>
            </div>
          </div>
          
          {/* Action Button */}
          <button className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium flex items-center justify-center space-x-2 transition-colors">
            <span>Continue to AWS Setup</span>
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>
        
        {/* Bottom Features */}
        <div className="mt-6 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400">
            <div className="flex items-center space-x-1">
              <Settings className="w-3 h-3" />
              <span>Auto-configured</span>
            </div>
            <div className="flex items-center space-x-1">
              <Globe className="w-3 h-3" />
              <span>Global CDN</span>
            </div>
            <div className="flex items-center space-x-1">
              <CheckCircle className="w-3 h-3" />
              <span>SSL Enabled</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
