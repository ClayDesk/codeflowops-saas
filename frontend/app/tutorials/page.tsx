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

  const videoTutorials = [
    {
      id: 'main-demo',
      title: 'CodeFlowOps Complete Demo - Deploy Static Sites in Minutes',
      description: 'Watch how CodeFlowOps automatically analyzes, builds, and deploys your static websites to AWS with zero configuration.',
      duration: '8:30',
      thumbnail: '/api/placeholder/640/360',
      youtubeId: 'YOUR_YOUTUBE_VIDEO_ID', // Replace with actual YouTube video ID
      featured: true,
      views: '12.5K',
      category: 'static'
    },
    {
      id: 'react-deploy',
      title: 'Deploy React Applications with CodeFlowOps',
      description: 'Step-by-step guide to deploying React apps including Next.js, Vite, and Create React App projects.',
      duration: '10:15',
      thumbnail: '/api/placeholder/640/360',
      youtubeId: 'REACT_DEMO_VIDEO_ID',
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

  const VideoCard = ({ video }: { video: typeof videoTutorials[0] }) => (
    <Card className="group hover:shadow-lg transition-all duration-300 dark:bg-gray-800 dark:border-gray-700">
      <div className="relative">
        <div className="aspect-video bg-gray-100 dark:bg-gray-700 rounded-t-lg overflow-hidden">
          <div className="w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
            <Play className="h-16 w-16 text-white opacity-80 group-hover:opacity-100 transition-opacity" />
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
      </div>
      <CardHeader className="pb-3">
        <CardTitle className="text-lg group-hover:text-blue-600 dark:group-hover:text-blue-400 transition-colors">
          {video.title}
        </CardTitle>
        <CardDescription className="text-sm line-clamp-2">
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
        <Button className="w-full group-hover:bg-blue-600 transition-colors">
          <Play className="h-4 w-4 mr-2" />
          Watch Tutorial
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
              Master static site and React deployment with our comprehensive video tutorials
            </p>
            <div className="flex flex-col sm:flex-row gap-4 justify-center">
              <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
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
        <div className="mb-12">
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
              <div className="w-full h-full bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center">
                <div className="text-center text-white">
                  <Play className="h-20 w-20 mx-auto mb-4 opacity-80" />
                  <h3 className="text-2xl font-bold mb-2">CodeFlowOps Static Site Demo</h3>
                  <p className="text-blue-100 mb-4">See how to deploy static websites in under 3 minutes</p>
                  <Button size="lg" className="bg-white text-blue-600 hover:bg-gray-100">
                    <Play className="h-5 w-5 mr-2" />
                    Watch Now (8:30)
                  </Button>
                </div>
              </div>
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
