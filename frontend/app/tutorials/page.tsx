'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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

  const videoTutorials = [
    {
      id: 'react-demo',
      title: 'Deploy React Applications with CodeFlowOps',
      description: 'Complete walkthrough of deploying React apps including Next.js, Vite, and Create React App projects with real-time monitoring and automated deployments.',
      duration: 'Live Demo',
      youtubeId: 'E-6KSTq_k6o',
      featured: true,
      views: '2.1K',
      category: 'react',
      publishedDate: 'Sep 2024'
    },
    {
      id: 'static-demo',
      title: 'Deploy Static Sites in Minutes - CodeFlowOps Demo',
      description: 'See how CodeFlowOps automatically analyzes, builds, and deploys your static websites to AWS with zero configuration required.',
      duration: 'Live Demo',
      youtubeId: 'fDp5-NGNEqo',
      views: '1.8K',
      category: 'static',
      publishedDate: 'Sep 2024'
    }
  ]

  const categories = [
    { id: 'all', name: 'All Tutorials', icon: Rocket },
    { id: 'react', name: 'React Apps', icon: Code },
    { id: 'static', name: 'Static Sites', icon: Globe }
  ]

  const filteredVideos = activeCategory === 'all' ? videoTutorials : videoTutorials.filter(video => video.category === activeCategory)
  const featuredVideo = videoTutorials.find(video => video.featured)

  const VideoEmbed = ({ youtubeId, title }: { youtubeId: string, title: string }) => (
    <div className="aspect-video w-full">
      <iframe
        src={`https://www.youtube.com/embed/${youtubeId}?rel=0&modestbranding=1`}
        title={title}
        frameBorder="0"
        allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share"
        allowFullScreen
        className="w-full h-full rounded-lg"
      />
    </div>
  )

  const VideoCard = ({ video }: { video: typeof videoTutorials[0] }) => (
    <Card className="group hover:shadow-lg transition-all duration-300 dark:bg-gray-800 dark:border-gray-700">
      <div className="relative">
        <VideoEmbed youtubeId={video.youtubeId} title={video.title} />
        {video.featured && (
          <Badge className="absolute top-3 left-3 bg-red-500 text-white">
            <Star className="h-3 w-3 mr-1" />
            Featured
          </Badge>
        )}
      </div>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
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
          <span className="text-xs">{video.publishedDate}</span>
        </div>
        <Button 
          className="w-full group-hover:bg-blue-600 transition-colors"
          onClick={() => window.open(`https://www.youtube.com/watch?v=${video.youtubeId}`, '_blank')}
        >
          <ExternalLink className="h-4 w-4 mr-2" />
          Watch on YouTube
        </Button>
      </CardContent>
    </Card>
  )

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900">
      {/* Hero Section */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-700 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-16">
          <div className="text-center">
            <h1 className="text-4xl md:text-5xl font-bold mb-6">
              Learn CodeFlowOps
            </h1>
            <p className="text-xl md:text-2xl mb-8 text-blue-100 max-w-3xl mx-auto">
              Watch live demos and learn how to deploy React apps and static sites in minutes
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button 
                size="lg" 
                className="bg-white text-blue-600 hover:bg-gray-100"
                onClick={() => document.getElementById('featured-video')?.scrollIntoView({ behavior: 'smooth' })}
              >
                <Play className="h-5 w-5 mr-2" />
                Watch React Demo
              </Button>
              <Button 
                size="lg" 
                variant="outline" 
                className="border-white text-white hover:bg-white hover:text-blue-600"
                onClick={() => window.open('https://docs.codeflowops.com', '_blank')}
              >
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
        {featuredVideo && (
          <div id="featured-video" className="mb-12">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-gray-900 dark:text-white mb-4">
                🚀 Featured Demo: React Deployment
              </h2>
              <p className="text-lg text-gray-600 dark:text-gray-400">
                Watch how to deploy React applications with real-time monitoring and automated builds
              </p>
            </div>
            
            <Card className="max-w-5xl mx-auto overflow-hidden shadow-xl dark:bg-gray-800 dark:border-gray-700">
              <div className="p-6">
                <VideoEmbed youtubeId={featuredVideo.youtubeId} title={featuredVideo.title} />
                <div className="mt-6">
                  <div className="flex items-center justify-between mb-4">
                    <h3 className="text-2xl font-bold text-gray-900 dark:text-white">
                      {featuredVideo.title}
                    </h3>
                    <Badge className="bg-red-500 text-white">
                      <Star className="h-3 w-3 mr-1" />
                      Featured
                    </Badge>
                  </div>
                  <p className="text-gray-600 dark:text-gray-400 mb-4">
                    {featuredVideo.description}
                  </p>
                  <div className="flex items-center gap-6 text-sm text-gray-500 dark:text-gray-400">
                    <span className="flex items-center gap-1">
                      <Users className="h-4 w-4" />
                      {featuredVideo.views} views
                    </span>
                    <span className="flex items-center gap-1">
                      <Clock className="h-4 w-4" />
                      {featuredVideo.publishedDate}
                    </span>
                    <Button 
                      variant="outline" 
                      size="sm"
                      onClick={() => window.open(`https://www.youtube.com/watch?v=${featuredVideo.youtubeId}`, '_blank')}
                    >
                      <ExternalLink className="h-4 w-4 mr-2" />
                      Watch on YouTube
                    </Button>
                  </div>
                </div>
              </div>
            </Card>
          </div>
        )}

        {/* Tutorial Categories */}
        <div className="mb-8">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-6">
            All Video Tutorials
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
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8 mb-16">
          {filteredVideos.map((video) => (
            <VideoCard key={video.id} video={video} />
          ))}
        </div>

        {/* Additional Resources */}
        <div className="border-t border-gray-200 dark:border-gray-700 pt-12">
          <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-8 text-center">
            Additional Resources
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <Card className="text-center p-6 dark:bg-gray-800 dark:border-gray-700">
              <BookOpen className="h-12 w-12 mx-auto mb-4 text-blue-600" />
              <h3 className="text-xl font-bold mb-2 dark:text-white">Documentation</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Comprehensive guides, API references, and deployment configurations
              </p>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => window.open('https://docs.codeflowops.com', '_blank')}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                View Docs
              </Button>
            </Card>

            <Card className="text-center p-6 dark:bg-gray-800 dark:border-gray-700">
              <Github className="h-12 w-12 mx-auto mb-4 text-blue-600" />
              <h3 className="text-xl font-bold mb-2 dark:text-white">Example Projects</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Ready-to-deploy sample applications and starter templates
              </p>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => window.open('https://github.com/codeflowops/examples', '_blank')}
              >
                <Download className="h-4 w-4 mr-2" />
                Get Examples
              </Button>
            </Card>

            <Card className="text-center p-6 dark:bg-gray-800 dark:border-gray-700">
              <Users className="h-12 w-12 mx-auto mb-4 text-blue-600" />
              <h3 className="text-xl font-bold mb-2 dark:text-white">Community Support</h3>
              <p className="text-gray-600 dark:text-gray-400 mb-4">
                Join our developer community for help and best practices
              </p>
              <Button 
                variant="outline" 
                className="w-full"
                onClick={() => window.open('/contact', '_blank')}
              >
                <ExternalLink className="h-4 w-4 mr-2" />
                Get Support
              </Button>
            </Card>
          </div>
        </div>
      </div>
    </div>
  )
}
