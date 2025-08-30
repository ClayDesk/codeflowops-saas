'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { 
  Play, 
  Clock, 
  Users, 
  BookOpen, 
  Code, 
  Rocket, 
  Globe, 
  Github,
  ExternalLink,
  ChevronRight,
  Star,
  Download
} from 'lucide-react'

export default function TutorialsPage() {
  const [activeCategory, setActiveCategory] = useState('all')
  const [showFeaturedVideo, setShowFeaturedVideo] = useState(false)
  const [featuredVideoLoading, setFeaturedVideoLoading] = useState(false)
  const [debugClicks, setDebugClicks] = useState(0)

  const handleFeaturedVideoPlay = (e?: React.MouseEvent) => {
    if (e) {
      e.preventDefault()
      e.stopPropagation()
    }
    console.log('Featured video clicked!')
    alert('Featured video clicked!') // Debug alert
    setDebugClicks(prev => prev + 1)
    setFeaturedVideoLoading(true)
    setShowFeaturedVideo(true)
  }

  const handleOpenFeaturedInNewTab = () => {
    console.log('Opening featured video in new tab')
    alert('Opening YouTube') // Debug alert
    window.open('https://www.youtube.com/watch?v=fDp5-NGNEqo', '_blank')
  }

  const videoTutorials = [
    {
      id: 'static-demo',
      title: 'CodeFlowOps Static Site Demo - Deploy in Minutes',
      description: 'Watch how CodeFlowOps automatically analyzes, builds, and deploys your static websites to AWS with zero configuration.',
      duration: '8:30',
      thumbnail: 'https://img.youtube.com/vi/fDp5-NGNEqo/maxresdefault.jpg',
      youtubeId: 'fDp5-NGNEqo',
      featured: true,
      views: '12.5K',
      category: 'static'
    },
    {
      id: 'react-demo',
      title: 'Deploy React Applications with CodeFlowOps',
      description: 'Step-by-step guide to deploying React apps including Next.js, Vite, and Create React App projects.',
      duration: '8:30',
      thumbnail: 'https://img.youtube.com/vi/fDp5-NGNEqo/maxresdefault.jpg',
      youtubeId: 'fDp5-NGNEqo',
      views: '8.7K',
      category: 'react'
    }
  ]

  const categories = [
    { id: 'all', name: 'All Tutorials', icon: Rocket },
    { id: 'static', name: 'Static Sites', icon: Globe },
    { id: 'react', name: 'React Apps', icon: Code }
  ]

  const filteredVideos = activeCategory === 'all' ? videoTutorials : videoTutorials.filter(video => video.category === activeCategory)

  const VideoCard = ({ video }: { video: typeof videoTutorials[0] }) => {
    const [showVideo, setShowVideo] = useState(false)
    const [isLoading, setIsLoading] = useState(false)
    
    const handlePlayVideo = (e: React.MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      console.log(`Playing video: ${video.title}`)
      alert(`Playing video: ${video.title}`) // Debug alert
      setIsLoading(true)
      setShowVideo(true)
    }

    const handleOpenInNewTab = (e: React.MouseEvent) => {
      e.preventDefault()
      e.stopPropagation()
      console.log('Opening video in new tab')
      alert('Opening YouTube') // Debug alert
      window.open(`https://www.youtube.com/watch?v=${video.youtubeId}`, '_blank')
    }
    
    return (
      <Card className="overflow-hidden dark:bg-gray-800 dark:border-gray-700">
        <div className="aspect-video bg-gray-100 dark:bg-gray-700">
          {showVideo ? (
            <div className="relative w-full h-full">
              <iframe
                src={`https://www.youtube.com/embed/${video.youtubeId}?autoplay=1&rel=0`}
                title={video.title}
                className="w-full h-full"
                frameBorder="0"
                allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                allowFullScreen
                onLoad={() => setIsLoading(false)}
              />
              {isLoading && (
                <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                  <div className="text-white">Loading video...</div>
                </div>
              )}
            </div>
          ) : (
            <div className="relative w-full h-full cursor-pointer" onClick={handlePlayVideo}>
              <img 
                src={video.thumbnail}
                alt={video.title}
                className="w-full h-full object-cover"
              />
              <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
                <button
                  onClick={handlePlayVideo}
                  className="bg-red-600 hover:bg-red-700 rounded-full p-4 transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-red-500"
                  aria-label={`Play ${video.title}`}
                >
                  <Play className="h-12 w-12 text-white ml-1" />
                </button>
              </div>
              {video.featured && (
                <Badge className="absolute top-3 left-3 bg-red-500 text-white">
                  <Star className="h-3 w-3 mr-1" />
                  Featured
                </Badge>
              )}
              <div className="absolute bottom-3 right-3 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                {video.duration}
              </div>
            </div>
          )}
        </div>
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">
            {video.title}
          </CardTitle>
          <CardDescription className="text-sm">
            {video.description}
          </CardDescription>
        </CardHeader>
        <CardContent className="pt-0">
          <div className="flex items-center justify-between text-sm text-gray-500 dark:text-gray-400 mb-4">
            <div className="flex items-center gap-4">
              <span className="flex items-center gap-1">
                <Clock className="h-4 w-4" />
                {video.duration}
              </span>
              <span className="flex items-center gap-1">
                <Users className="h-4 w-4" />
                {video.views} views
              </span>
            </div>
          </div>
          <div className="flex gap-2">
            <Button 
              className="flex-1"
              onClick={handlePlayVideo}
              disabled={isLoading}
            >
              <Play className="h-4 w-4 mr-2" />
              {showVideo ? 'Playing...' : isLoading ? 'Loading...' : 'Watch Here'}
            </Button>
            <Button 
              variant="outline"
              onClick={handleOpenInNewTab}
              className="px-3"
              title="Open in YouTube"
            >
              <ExternalLink className="h-4 w-4" />
            </Button>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Debug info - remove in production */}
      <div className="fixed top-4 right-4 bg-black text-white p-2 rounded text-xs z-50">
        Featured Video: {showFeaturedVideo ? 'ON' : 'OFF'} | Clicks: {debugClicks}
        <br />
        <button 
          onClick={() => alert('Test button works!')}
          className="bg-red-500 text-white px-2 py-1 mt-1 rounded text-xs"
        >
          TEST CLICK
        </button>
      </div>
      
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              Learn CodeFlowOps
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
              Master static site and React deployment with our comprehensive video tutorials
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg" 
                className="bg-white text-blue-600 hover:bg-gray-100"
                onClick={() => {
                  console.log('Hero button clicked!')
                  handleFeaturedVideoPlay()
                  // Scroll to featured video section
                  document.getElementById('featured-video')?.scrollIntoView({ 
                    behavior: 'smooth' 
                  })
                }}
              >
                <Play className="h-5 w-5 mr-2" />
                Watch Main Demo
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-blue-600">
                <BookOpen className="h-5 w-5 mr-2" />
                Documentation
              </Button>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Featured Video */}
        <div className="mb-12" id="featured-video">
          <div className="text-center mb-8">
            <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
              Featured Tutorial
            </h2>
            <p className="text-lg text-gray-600 dark:text-gray-400">
              Learn how to deploy static sites and React applications with CodeFlowOps
            </p>
          </div>
          
          <Card className="max-w-4xl mx-auto overflow-hidden shadow-xl dark:bg-gray-800 dark:border-gray-700">
            <div className="aspect-video bg-gray-100 dark:bg-gray-700">
              {showFeaturedVideo ? (
                <div className="relative w-full h-full">
                  <iframe
                    src="https://www.youtube.com/embed/fDp5-NGNEqo?autoplay=1&rel=0"
                    title="CodeFlowOps Static Site Demo"
                    className="w-full h-full"
                    frameBorder="0"
                    allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
                    allowFullScreen
                    onLoad={() => setFeaturedVideoLoading(false)}
                  />
                  {featuredVideoLoading && (
                    <div className="absolute inset-0 bg-black bg-opacity-50 flex items-center justify-center">
                      <div className="text-white">Loading video...</div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="relative w-full h-full cursor-pointer" onClick={handleFeaturedVideoPlay}>
                  <img 
                    src="https://img.youtube.com/vi/fDp5-NGNEqo/maxresdefault.jpg"
                    alt="CodeFlowOps Demo"
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute inset-0 bg-black bg-opacity-40 flex items-center justify-center">
                    <div className="text-center text-white">
                      <button
                        onClick={handleFeaturedVideoPlay}
                        className="bg-red-600 hover:bg-red-700 rounded-full p-6 mx-auto mb-4 transition-all hover:scale-110 focus:outline-none focus:ring-2 focus:ring-red-500"
                        aria-label="Play CodeFlowOps demo video"
                      >
                        <Play className="h-12 w-12 text-white ml-1" />
                      </button>
                      <h3 className="text-2xl font-bold mb-2">CodeFlowOps Static Site Demo</h3>
                      <p className="text-blue-100 mb-4">See how to deploy static websites in under 3 minutes</p>
                      <div className="flex gap-2 justify-center">
                        <Button 
                          size="lg" 
                          className="bg-white text-blue-600 hover:bg-gray-100"
                          onClick={handleFeaturedVideoPlay}
                          disabled={featuredVideoLoading}
                        >
                          <Play className="h-5 w-5 mr-2" />
                          {featuredVideoLoading ? 'Loading...' : 'Watch Now (8:30)'}
                        </Button>
                        <Button 
                          size="lg"
                          variant="outline"
                          className="border-white text-white hover:bg-white hover:text-blue-600"
                          onClick={handleOpenFeaturedInNewTab}
                        >
                          <ExternalLink className="h-5 w-5 mr-2" />
                          YouTube
                        </Button>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </Card>
        </div>

        {/* Tutorial Categories */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            Tutorial Categories
          </h2>
          
          <div className="flex flex-wrap gap-3 mb-8">
            {categories.map((category) => (
              <Button
                key={category.id}
                variant={activeCategory === category.id ? "default" : "outline"}
                onClick={() => setActiveCategory(category.id)}
                className="flex items-center gap-2"
              >
                <category.icon className="h-4 w-4" />
                {category.name}
              </Button>
            ))}
          </div>
        </div>

        {/* Video Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredVideos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>

        {/* Additional Resources */}
        <div className="mt-16 grid grid-cols-1 md:grid-cols-3 gap-6">
          <Card className="text-center p-6 dark:bg-gray-800 dark:border-gray-700">
            <BookOpen className="h-12 w-12 mx-auto mb-4 text-blue-600" />
            <h3 className="text-xl font-bold mb-2 dark:text-white">Documentation</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Comprehensive guides and API references
            </p>
            <Button variant="outline" className="w-full">
              <ExternalLink className="h-4 w-4 mr-2" />
              View Docs
            </Button>
          </Card>

          <Card className="text-center p-6 dark:bg-gray-800 dark:border-gray-700">
            <Github className="h-12 w-12 mx-auto mb-4 text-blue-600" />
            <h3 className="text-xl font-bold mb-2 dark:text-white">Example Projects</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Ready-to-deploy sample applications
            </p>
            <Button variant="outline" className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Get Examples
            </Button>
          </Card>

          <Card className="text-center p-6 dark:bg-gray-800 dark:border-gray-700">
            <Users className="h-12 w-12 mx-auto mb-4 text-blue-600" />
            <h3 className="text-xl font-bold mb-2 dark:text-white">Community</h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Join our developer community for support
            </p>
            <Button variant="outline" className="w-full">
              <ExternalLink className="h-4 w-4 mr-2" />
              Join Discord
            </Button>
          </Card>
        </div>
      </div>
    </div>
  )
}
