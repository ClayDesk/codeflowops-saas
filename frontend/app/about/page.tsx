'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Users, 
  Target, 
  Heart, 
  Code, 
  Rocket, 
  Globe, 
  Award, 
  Lightbulb, 
  Shield, 
  Zap,
  Building,
  MapPin,
  Mail,
  Calendar,
  CheckCircle,
  Star,
  ArrowRight,
  Github,
  Linkedin,
  Twitter,
  Coffee,
  Clock,
  TrendingUp,
  Cpu,
  Database,
  CloudCog,
  Sparkles,
  Flag,
  BookOpen,
  GraduationCap
} from 'lucide-react'

export default function AboutPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full shadow-lg">
              <Rocket className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            About CodeFlowOps
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed">
            Revolutionizing software deployment with AI-powered automation, 
            making enterprise-grade DevOps accessible to every developer and team.
          </p>
        </div>

        {/* Mission & Vision */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Target className="h-6 w-6 mr-3 text-blue-600" />
                Our Mission
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                To democratize DevOps by providing intelligent, automated deployment solutions 
                that eliminate complexity and accelerate innovation. We believe every developer 
                should have access to enterprise-grade infrastructure without the enterprise-grade complexity.
              </p>
            </CardContent>
          </Card>
          
          <Card className="bg-gradient-to-br from-purple-50 to-pink-100 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200">
            <CardHeader>
              <CardTitle className="flex items-center text-xl">
                <Lightbulb className="h-6 w-6 mr-3 text-purple-600" />
                Our Vision
              </CardTitle>
            </CardHeader>
            <CardContent>
              <p className="text-slate-700 dark:text-slate-300 leading-relaxed">
                A world where deployment friction is eliminated, where ideas become reality 
                in minutes not months, and where developers can focus on building amazing 
                products instead of wrestling with infrastructure.
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Company Story */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <BookOpen className="h-7 w-7 mr-3" />
              Our Story
            </CardTitle>
            <CardDescription>
              How CodeFlowOps came to life
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="prose prose-slate dark:prose-invert max-w-none">
              <p className="text-lg leading-relaxed">
                CodeFlowOps was born from a simple frustration: why should deploying great software be so complicated? 
                Our founders, seasoned engineers who had spent countless hours battling deployment pipelines at 
                Fortune 500 companies, knew there had to be a better way.
              </p>
              
              <p className="leading-relaxed">
                In 2024, we set out to build the deployment platform we wished we had – one that understands your code, 
                predicts your needs, and automates the complexity away. What started as a weekend project to solve 
                our own deployment headaches has evolved into a comprehensive platform trusted by developers worldwide.
              </p>
              
              <p className="leading-relaxed">
                Today, CodeFlowOps powers thousands of deployments daily, from solo developers shipping their first 
                app to enterprise teams managing complex microservices architectures. Our AI-powered approach means 
                the platform gets smarter with every deployment, continuously learning and optimizing for better performance.
              </p>
            </div>
            
            {/* Timeline */}
            <div className="bg-slate-50 dark:bg-slate-800/50 rounded-lg p-6 mt-8">
              <h4 className="font-semibold text-lg mb-4 flex items-center">
                <Calendar className="h-5 w-5 mr-2" />
                Key Milestones
              </h4>
              <div className="space-y-4">
                <div className="flex items-center space-x-4">
                  <div className="w-3 h-3 bg-blue-600 rounded-full flex-shrink-0"></div>
                  <div>
                    <div className="font-medium">Q1 2024 - Foundation</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">Company founded, initial AI deployment engine developed</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-3 h-3 bg-green-600 rounded-full flex-shrink-0"></div>
                  <div>
                    <div className="font-medium">Q2 2024 - First Beta</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">Launched closed beta with 100 developers</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-3 h-3 bg-purple-600 rounded-full flex-shrink-0"></div>
                  <div>
                    <div className="font-medium">Q3 2024 - Public Launch</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">Public platform launch with multi-cloud support</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-3 h-3 bg-orange-600 rounded-full flex-shrink-0"></div>
                  <div>
                    <div className="font-medium">Q4 2024 - Enterprise</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">Enterprise features, SOC 2 compliance, 1000+ customers</div>
                  </div>
                </div>
                <div className="flex items-center space-x-4">
                  <div className="w-3 h-3 bg-red-600 rounded-full flex-shrink-0"></div>
                  <div>
                    <div className="font-medium">2025 - Scale & Innovation</div>
                    <div className="text-sm text-slate-600 dark:text-slate-400">AI-powered optimization, global expansion, advanced analytics</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Our Values */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Heart className="h-7 w-7 mr-3" />
              Our Core Values
            </CardTitle>
            <CardDescription>
              The principles that guide everything we do
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-gradient-to-b from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
                <Zap className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Simplicity First</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Complex problems deserve simple solutions. We obsess over removing friction and making the hard things easy.
                </p>
              </div>
              
              <div className="text-center p-6 bg-gradient-to-b from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
                <Shield className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Security by Design</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Security isn't an afterthought—it's built into every line of code, every feature, every decision we make.
                </p>
              </div>
              
              <div className="text-center p-6 bg-gradient-to-b from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg">
                <Users className="h-12 w-12 text-purple-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Developer-Centric</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  We're developers building for developers. Every feature is designed with the developer experience in mind.
                </p>
              </div>
              
              <div className="text-center p-6 bg-gradient-to-b from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-lg">
                <TrendingUp className="h-12 w-12 text-yellow-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Continuous Innovation</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Technology evolves rapidly, and so do we. We're always pushing boundaries and exploring new possibilities.
                </p>
              </div>
              
              <div className="text-center p-6 bg-gradient-to-b from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-lg">
                <Globe className="h-12 w-12 text-red-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Global Impact</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Great software can change the world. We're here to help developers make that impact, anywhere, anytime.
                </p>
              </div>
              
              <div className="text-center p-6 bg-gradient-to-b from-indigo-50 to-indigo-100 dark:from-indigo-900/20 dark:to-indigo-800/20 rounded-lg">
                <Sparkles className="h-12 w-12 text-indigo-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Quality Excellence</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  We don't just ship code—we ship experiences. Every detail matters, from performance to polish.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Leadership Team */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Users className="h-7 w-7 mr-3" />
              Leadership Team
            </CardTitle>
            <CardDescription>
              Meet the people driving CodeFlowOps forward
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {/* CEO */}
              <div className="text-center p-6 border rounded-lg hover:shadow-lg transition-shadow">
                <div className="w-24 h-24 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">AK</span>
                </div>
                <h3 className="font-bold text-lg">Alex Kumar</h3>
                <p className="text-blue-600 font-medium mb-2">CEO & Co-Founder</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Former Principal Engineer at Amazon Web Services. 15+ years building scalable cloud infrastructure.
                </p>
                <div className="flex justify-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Linkedin className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Twitter className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* CTO */}
              <div className="text-center p-6 border rounded-lg hover:shadow-lg transition-shadow">
                <div className="w-24 h-24 bg-gradient-to-br from-green-500 to-teal-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">SC</span>
                </div>
                <h3 className="font-bold text-lg">Sarah Chen</h3>
                <p className="text-green-600 font-medium mb-2">CTO & Co-Founder</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  AI/ML expert from Google Brain. PhD in Computer Science, specialized in distributed systems.
                </p>
                <div className="flex justify-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Linkedin className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Github className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* VP Engineering */}
              <div className="text-center p-6 border rounded-lg hover:shadow-lg transition-shadow">
                <div className="w-24 h-24 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">MR</span>
                </div>
                <h3 className="font-bold text-lg">Michael Rodriguez</h3>
                <p className="text-purple-600 font-medium mb-2">VP of Engineering</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Former Staff Engineer at Netflix. Expert in microservices architecture and platform engineering.
                </p>
                <div className="flex justify-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Linkedin className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Github className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* VP Product */}
              <div className="text-center p-6 border rounded-lg hover:shadow-lg transition-shadow">
                <div className="w-24 h-24 bg-gradient-to-br from-orange-500 to-red-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">EP</span>
                </div>
                <h3 className="font-bold text-lg">Emily Park</h3>
                <p className="text-orange-600 font-medium mb-2">VP of Product</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Product leader from Stripe. 12+ years designing developer tools and platform experiences.
                </p>
                <div className="flex justify-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Linkedin className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Twitter className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Head of Security */}
              <div className="text-center p-6 border rounded-lg hover:shadow-lg transition-shadow">
                <div className="w-24 h-24 bg-gradient-to-br from-red-500 to-pink-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">DT</span>
                </div>
                <h3 className="font-bold text-lg">David Thompson</h3>
                <p className="text-red-600 font-medium mb-2">Head of Security</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Cybersecurity veteran from CrowdStrike. CISSP certified with expertise in cloud security.
                </p>
                <div className="flex justify-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Linkedin className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Twitter className="h-4 w-4" />
                  </Button>
                </div>
              </div>

              {/* Head of Customer Success */}
              <div className="text-center p-6 border rounded-lg hover:shadow-lg transition-shadow">
                <div className="w-24 h-24 bg-gradient-to-br from-teal-500 to-blue-600 rounded-full mx-auto mb-4 flex items-center justify-center">
                  <span className="text-white font-bold text-2xl">LW</span>
                </div>
                <h3 className="font-bold text-lg">Lisa Wang</h3>
                <p className="text-teal-600 font-medium mb-2">Head of Customer Success</p>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Customer experience leader from Atlassian. Passionate about developer relations and community building.
                </p>
                <div className="flex justify-center space-x-2">
                  <Button variant="outline" size="sm">
                    <Linkedin className="h-4 w-4" />
                  </Button>
                  <Button variant="outline" size="sm">
                    <Twitter className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Technology & Innovation */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Cpu className="h-7 w-7 mr-3" />
              Technology & Innovation
            </CardTitle>
            <CardDescription>
              The cutting-edge tech powering our platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h4 className="font-semibold text-lg mb-4 flex items-center">
                  <Code className="h-5 w-5 mr-2 text-blue-600" />
                  Core Technologies
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-3" />
                    <span>AI-powered deployment optimization</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-3" />
                    <span>Multi-cloud orchestration engine</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-3" />
                    <span>Real-time performance analytics</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-3" />
                    <span>Intelligent resource scaling</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-3" />
                    <span>Advanced security automation</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-lg mb-4 flex items-center">
                  <Lightbulb className="h-5 w-5 mr-2 text-purple-600" />
                  Innovation Areas
                </h4>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <Star className="h-4 w-4 text-purple-600 mr-3" />
                    <span>Machine learning deployment patterns</span>
                  </div>
                  <div className="flex items-center">
                    <Star className="h-4 w-4 text-purple-600 mr-3" />
                    <span>Predictive infrastructure optimization</span>
                  </div>
                  <div className="flex items-center">
                    <Star className="h-4 w-4 text-purple-600 mr-3" />
                    <span>Natural language deployment configuration</span>
                  </div>
                  <div className="flex items-center">
                    <Star className="h-4 w-4 text-purple-600 mr-3" />
                    <span>Autonomous incident resolution</span>
                  </div>
                  <div className="flex items-center">
                    <Star className="h-4 w-4 text-purple-600 mr-3" />
                    <span>Edge computing deployment optimization</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Company Stats */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <TrendingUp className="h-7 w-7 mr-3" />
              By the Numbers
            </CardTitle>
            <CardDescription>
              Our impact in the developer community
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
              <div className="text-center p-4 bg-gradient-to-b from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
                <div className="text-3xl font-bold text-blue-600 mb-2">10K+</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Active Developers</div>
              </div>
              <div className="text-center p-4 bg-gradient-to-b from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
                <div className="text-3xl font-bold text-green-600 mb-2">1M+</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Successful Deployments</div>
              </div>
              <div className="text-center p-4 bg-gradient-to-b from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg">
                <div className="text-3xl font-bold text-purple-600 mb-2">50+</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Countries Served</div>
              </div>
              <div className="text-center p-4 bg-gradient-to-b from-orange-50 to-orange-100 dark:from-orange-900/20 dark:to-orange-800/20 rounded-lg">
                <div className="text-3xl font-bold text-orange-600 mb-2">99.9%</div>
                <div className="text-sm text-slate-600 dark:text-slate-400">Platform Uptime</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Company Info */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Building className="h-7 w-7 mr-3" />
              Company Information
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h4 className="font-semibold text-lg mb-4">Contact Information</h4>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <Building className="h-4 w-4 mr-3 text-slate-500" />
                    <span>ClayDesk LLC</span>
                  </div>
                  <div className="flex items-start">
                    <MapPin className="h-4 w-4 mr-3 text-slate-500 mt-1" />
                    <div>
                      <div>45 Burgundy Hills Lane</div>
                      <div>Middletown, CT 06457</div>
                      <div>United States</div>
                    </div>
                  </div>
                  <div className="flex items-center">
                    <Mail className="h-4 w-4 mr-3 text-slate-500" />
                    <span>hello@claydesk.com</span>
                  </div>
                  <div className="flex items-center">
                    <Globe className="h-4 w-4 mr-3 text-slate-500" />
                    <span>www.codeflowops.com</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-lg mb-4">Company Details</h4>
                <div className="space-y-3">
                  <div className="flex justify-between">
                    <span className="text-slate-600 dark:text-slate-400">Founded</span>
                    <span className="font-medium">2024</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 dark:text-slate-400">Headquarters</span>
                    <span className="font-medium">Connecticut, USA</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 dark:text-slate-400">Company Type</span>
                    <span className="font-medium">Private LLC</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 dark:text-slate-400">Industry</span>
                    <span className="font-medium">DevOps & Cloud Infrastructure</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-slate-600 dark:text-slate-400">Employees</span>
                    <span className="font-medium">25-50</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Join Us */}
        <Card className="mb-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
          <CardContent className="p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Join the CodeFlowOps Journey</h2>
            <p className="text-xl mb-6 text-blue-100">
              Ready to shape the future of software deployment? We're always looking for passionate people to join our team.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button size="lg" variant="secondary" className="bg-white text-blue-600 hover:bg-blue-50">
                <Users className="h-5 w-5 mr-2" />
                View Open Positions
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                <Mail className="h-5 w-5 mr-2" />
                Contact Us
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            Thank you for taking the time to learn about CodeFlowOps. We're excited to be part of your development journey.
          </p>
          <p className="mt-2">
            Questions? Reach out to us at <a href="mailto:hello@claydesk.com" className="text-blue-600 hover:underline">hello@claydesk.com</a>
          </p>
          <p className="mt-4 font-semibold">
            © 2025 ClayDesk LLC. Built with ❤️ for developers worldwide.
          </p>
        </div>
      </div>
    </div>
  )
}
