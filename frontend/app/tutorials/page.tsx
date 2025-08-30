'use client'

import React from 'react'
import { Play, ExternalLink, Clock, Eye } from 'lucide-react'

export default function TutorialsPage() {
  const openVideo = (videoId: string, title: string) => {
    console.log(`Opening video: ${title}`)
    window.open(`https://www.youtube.com/watch?v=${videoId}`, '_blank')
  }

  const videos = [
    {
      id: 'fDp5-NGNEqo',
      title: 'CodeFlowOps Static Site Demo - Deploy in Minutes',
      description: 'Watch how CodeFlowOps automatically analyzes, builds, and deploys your static websites to AWS with zero configuration.',
      duration: '8:30',
      views: '12.5K',
      thumbnail: 'https://img.youtube.com/vi/fDp5-NGNEqo/maxresdefault.jpg'
    },
    {
      id: 'fDp5-NGNEqo',
      title: 'Deploy React Applications with CodeFlowOps',
      description: 'Step-by-step guide to deploying React apps including Next.js, Vite, and Create React App projects.',
      duration: '8:30',
      views: '8.7K',
      thumbnail: 'https://img.youtube.com/vi/fDp5-NGNEqo/maxresdefault.jpg'
    }
  ]

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-700 text-white py-16">
        <div className="max-w-4xl mx-auto px-4 text-center">
          <h1 className="text-4xl md:text-5xl font-bold mb-6">
            Learn CodeFlowOps
          </h1>
          <p className="text-xl mb-8 text-blue-100">
            Master static site and React deployment with our video tutorials
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-6xl mx-auto px-4 py-12">
        {/* Featured Video */}
        <div className="mb-12">
          <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-8 text-center">
            Featured Tutorial
          </h2>
          
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden max-w-4xl mx-auto">
            <div className="relative">
              <img 
                src="https://img.youtube.com/vi/fDp5-NGNEqo/maxresdefault.jpg"
                alt="CodeFlowOps Demo"
                className="w-full h-64 md:h-96 object-cover"
              />
              <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
                <button
                  onClick={() => openVideo('fDp5-NGNEqo', 'CodeFlowOps Demo')}
                  className="bg-red-600 hover:bg-red-700 rounded-full p-6 transition-all hover:scale-110 shadow-lg"
                >
                  <Play className="h-12 w-12 text-white ml-1" />
                </button>
              </div>
            </div>
            <div className="p-6">
              <h3 className="text-2xl font-bold mb-2 dark:text-white">
                CodeFlowOps Static Site Demo
              </h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                See how to deploy static websites in under 3 minutes with zero configuration
              </p>
              <div className="flex gap-4">
                <button
                  onClick={() => openVideo('fDp5-NGNEqo', 'CodeFlowOps Demo')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Play className="h-4 w-4" />
                  Watch Now (8:30)
                </button>
                <button
                  onClick={() => openVideo('fDp5-NGNEqo', 'CodeFlowOps Demo')}
                  className="border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 px-6 py-2 rounded-lg flex items-center gap-2 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                >
                  <ExternalLink className="h-4 w-4" />
                  Open in YouTube
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Video Grid */}
        <div className="mb-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-8">
            All Tutorials
          </h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {videos.map((video, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                <div className="relative">
                  <img 
                    src={video.thumbnail}
                    alt={video.title}
                    className="w-full h-48 object-cover"
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 hover:opacity-100 transition-opacity cursor-pointer"
                       onClick={() => openVideo(video.id, video.title)}>
                    <button className="bg-red-600 hover:bg-red-700 rounded-full p-4 transition-all hover:scale-110">
                      <Play className="h-8 w-8 text-white ml-1" />
                    </button>
                  </div>
                  <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                    {video.duration}
                  </div>
                </div>
                <div className="p-4">
                  <h3 className="text-lg font-bold mb-2 dark:text-white">
                    {video.title}
                  </h3>
                  <p className="text-gray-600 dark:text-gray-400 text-sm mb-4">
                    {video.description}
                  </p>
                  <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
                    <div className="flex items-center gap-4">
                      <span className="flex items-center gap-1">
                        <Clock className="h-4 w-4" />
                        {video.duration}
                      </span>
                      <span className="flex items-center gap-1">
                        <Eye className="h-4 w-4" />
                        {video.views} views
                      </span>
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <button
                      onClick={() => openVideo(video.id, video.title)}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
                    >
                      <Play className="h-4 w-4" />
                      Watch Tutorial
                    </button>
                    <button
                      onClick={() => openVideo(video.id, video.title)}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Additional Resources */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
            <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="h-6 w-6 text-blue-600 dark:text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.246 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
              </svg>
            </div>
            <h3 className="text-lg font-bold mb-2 dark:text-white">Documentation</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
              Comprehensive guides and API references
            </p>
            <button className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              View Docs
            </button>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
            <div className="w-12 h-12 bg-green-100 dark:bg-green-900 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="h-6 w-6 text-green-600 dark:text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold mb-2 dark:text-white">Example Projects</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
              Ready-to-deploy sample applications
            </p>
            <button className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              Get Examples
            </button>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6 text-center">
            <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900 rounded-lg flex items-center justify-center mx-auto mb-4">
              <svg className="h-6 w-6 text-purple-600 dark:text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
              </svg>
            </div>
            <h3 className="text-lg font-bold mb-2 dark:text-white">Community</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4 text-sm">
              Join our developer community for support
            </p>
            <button className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors">
              Join Discord
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
