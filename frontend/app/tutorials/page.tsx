'use client'

import React, { useState } from 'react'
import { Play, ExternalLink, Clock, Eye } from 'lucide-react'

export default function TutorialsPage() {
  const [playingVideos, setPlayingVideos] = useState<{ [key: string]: boolean }>({})

  const playVideo = (videoId: string) => {
    setPlayingVideos(prev => ({ ...prev, [videoId]: true }))
  }

  const openInYoutube = (videoId: string, title: string) => {
    console.log(`Opening video in YouTube: ${title}`)
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
    },
    {
      id: 'fDp5-NGNEqo',
      title: 'Laravel Deployment with CodeFlowOps',
      description: 'Complete guide to deploying Laravel applications with automatic database setup and SSL certificates.',
      duration: '12:15',
      views: '6.2K',
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
            Master deployment automation with our step-by-step video tutorials
          </p>
          <button
            onClick={() => playVideo('featured')}
            className="bg-white text-blue-600 hover:bg-gray-100 px-8 py-3 rounded-lg font-semibold flex items-center gap-2 mx-auto transition-colors"
          >
            <Play className="h-5 w-5" />
            Watch Main Demo
          </button>
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
            <div className="aspect-video bg-gray-100 dark:bg-gray-700">
              {playingVideos['featured'] ? (
                <iframe
                  src="https://www.youtube.com/embed/fDp5-NGNEqo?autoplay=1&rel=0"
                  title="CodeFlowOps Static Site Demo"
                  className="w-full h-full"
                  frameBorder="0"
                  allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                  allowFullScreen
                />
              ) : (
                <div 
                  className="relative cursor-pointer group w-full h-full"
                  onClick={() => playVideo('featured')}
                >
                  <img 
                    src="https://img.youtube.com/vi/fDp5-NGNEqo/maxresdefault.jpg"
                    alt="CodeFlowOps Demo"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center group-hover:bg-opacity-50 transition-all">
                    <button className="bg-red-600 hover:bg-red-700 rounded-full p-6 transition-all hover:scale-110 shadow-lg">
                      <Play className="h-12 w-12 text-white ml-1" />
                    </button>
                  </div>
                </div>
              )}
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
                  onClick={() => playVideo('featured')}
                  className="bg-blue-600 hover:bg-blue-700 text-white px-6 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Play className="h-4 w-4" />
                  {playingVideos['featured'] ? 'Playing...' : 'Watch Now (8:30)'}
                </button>
                <button
                  onClick={() => openInYoutube('fDp5-NGNEqo', 'CodeFlowOps Demo')}
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
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {videos.map((video, index) => (
              <div key={index} className="bg-white dark:bg-gray-800 rounded-lg shadow-lg overflow-hidden">
                <div className="aspect-video bg-gray-100 dark:bg-gray-700">
                  {playingVideos[video.id + index] ? (
                    <iframe
                      src={`https://www.youtube.com/embed/${video.id}?autoplay=1&rel=0`}
                      title={video.title}
                      className="w-full h-full"
                      frameBorder="0"
                      allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                      allowFullScreen
                    />
                  ) : (
                    <div 
                      className="relative cursor-pointer group w-full h-full"
                      onClick={() => playVideo(video.id + index)}
                    >
                      <img 
                        src={video.thumbnail}
                        alt={video.title}
                        className="w-full h-full object-cover"
                      />
                      <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity">
                        <button className="bg-red-600 hover:bg-red-700 rounded-full p-4 transition-all hover:scale-110">
                          <Play className="h-8 w-8 text-white ml-1" />
                        </button>
                      </div>
                      <div className="absolute bottom-2 right-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                        {video.duration}
                      </div>
                    </div>
                  )}
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
                      onClick={() => playVideo(video.id + index)}
                      className="flex-1 bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg flex items-center justify-center gap-2 transition-colors"
                    >
                      <Play className="h-4 w-4" />
                      {playingVideos[video.id + index] ? 'Playing...' : 'Watch Tutorial'}
                    </button>
                    <button
                      onClick={() => openInYoutube(video.id, video.title)}
                      className="px-3 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                      title="Open in YouTube"
                    >
                      <ExternalLink className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
