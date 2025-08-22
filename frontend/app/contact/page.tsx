'use client'

import React, { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Label } from '@/components/ui/label'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Mail, 
  Phone, 
  MapPin, 
  Clock, 
  MessageSquare, 
  Headphones, 
  Users, 
  Building, 
  Globe, 
  Send,
  CheckCircle,
  AlertCircle,
  Info,
  ArrowRight,
  ExternalLink,
  Github,
  Twitter,
  Linkedin,
  FileText,
  Book,
  Zap,
  Shield,
  Code,
  Heart,
  Calendar,
  Video,
  Smartphone,
  Slack,
  MessageCircle,
  HelpCircle,
  Star,
  Target,
  Briefcase,
  CreditCard,
  Settings,
  Bug,
  Lightbulb,
  Rocket,
  Volume2,
  Image
} from 'lucide-react'

export default function ContactPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    company: '',
    role: '',
    subject: '',
    message: '',
    inquiryType: ''
  })
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isSubmitted, setIsSubmitted] = useState(false)

  const handleInputChange = (field: string, value: string) => {
    setFormData(prev => ({ ...prev, [field]: value }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)
    
    // Simulate form submission
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    setIsSubmitting(false)
    setIsSubmitted(true)
  }

  const contactOptions = [
    {
      title: "Sales & Partnerships",
      description: "Questions about pricing, enterprise features, or partnership opportunities",
      email: "sales@codeflowops.com",
      phone: "+1 (555) 123-4567",
      icon: Briefcase,
      color: "blue",
      responseTime: "Within 4 hours"
    },
    {
      title: "Technical Support",
      description: "Get help with deployments, integrations, or technical issues",
      email: "support@codeflowops.com",
      phone: "+1 (555) 123-4568",
      icon: Headphones,
      color: "green",
      responseTime: "Within 2 hours"
    },
    {
      title: "Security & Compliance",
      description: "Security questionnaires, compliance documentation, and vulnerability reports",
      email: "security@codeflowops.com",
      phone: "+1 (555) 123-4569",
      icon: Shield,
      color: "red",
      responseTime: "Within 1 hour"
    },
    {
      title: "General Inquiries",
      description: "Media, press, general questions, or anything else",
      email: "hello@codeflowops.com",
      phone: "+1 (703) 646-3043",
      icon: MessageSquare,
      color: "purple",
      responseTime: "Within 8 hours"
    }
  ]

  const officeLocations = [
    {
      name: "Headquarters",
      address: "45 Burgundy Hills Lane",
      city: "Middletown, CT 06457",
      country: "United States",
      phone: "+1 (703) 646-3043",
      timezone: "EST (UTC-5)",
      hours: "9:00 AM - 6:00 PM EST"
    },
    {
      name: "European Office",
      address: "10 Tech Square",
      city: "London, SW1A 1AA",
      country: "United Kingdom",
      phone: "+44 20 7946 0958",
      timezone: "GMT (UTC+0)",
      hours: "9:00 AM - 6:00 PM GMT"
    },
    {
      name: "Asia-Pacific Office",
      address: "88 Market Street, #47-01",
      city: "Singapore 048948",
      country: "Singapore",
      phone: "+65 6123 4567",
      timezone: "SGT (UTC+8)",
      hours: "9:00 AM - 6:00 PM SGT"
    }
  ]

  const supportChannels = [
    {
      name: "Live Chat",
      description: "Instant help during business hours",
      icon: MessageCircle,
      available: "Mon-Fri, 9AM-6PM EST",
      action: "Start Chat"
    },
    {
      name: "Documentation",
      description: "Comprehensive guides and tutorials",
      icon: Book,
      available: "24/7",
      action: "Browse Docs"
    },
    {
      name: "Community Forum",
      description: "Connect with other developers",
      icon: Users,
      available: "24/7",
      action: "Join Forum"
    },
    {
      name: "Video Call",
      description: "Schedule a call with our team",
      icon: Video,
      available: "By appointment",
      action: "Schedule Call"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-green-500 to-teal-600 rounded-full shadow-lg">
              <MessageSquare className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Contact Us
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed mb-6">
            Have questions? Need help? Want to partner with us? 
            We'd love to hear from you. Our team is here to help.
          </p>
          <div className="flex items-center justify-center space-x-6 text-sm text-slate-500">
            <div className="flex items-center">
              <Clock className="h-4 w-4 mr-2" />
              <span>24/7 Support Available</span>
            </div>
            <div className="flex items-center">
              <MessageSquare className="h-4 w-4 mr-2" />
              <span>Average Response: 2 hours</span>
            </div>
            <div className="flex items-center">
              <Star className="h-4 w-4 mr-2" />
              <span>98% Customer Satisfaction</span>
            </div>
          </div>
        </div>

        {/* Quick Contact Options */}
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-6 mb-12">
          {contactOptions.map((option) => (
            <Card key={option.title} className="hover:shadow-lg transition-shadow">
              <CardContent className="p-6 text-center">
                <div className={`p-3 bg-${option.color}-100 dark:bg-${option.color}-900/20 rounded-full w-fit mx-auto mb-4`}>
                  <option.icon className={`h-8 w-8 text-${option.color}-600`} />
                </div>
                <h3 className="font-bold text-lg mb-2">{option.title}</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  {option.description}
                </p>
                <div className="space-y-2 mb-4">
                  <div className="flex items-center justify-center text-sm">
                    <Mail className="h-4 w-4 mr-2" />
                    <a href={`mailto:${option.email}`} className="text-blue-600 hover:underline">
                      {option.email}
                    </a>
                  </div>
                  <div className="flex items-center justify-center text-sm">
                    <Phone className="h-4 w-4 mr-2" />
                    <span>{option.phone}</span>
                  </div>
                </div>
                <Badge variant="outline" className="text-xs">
                  <Clock className="h-3 w-3 mr-1" />
                  {option.responseTime}
                </Badge>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid lg:grid-cols-2 gap-12 mb-12">
          {/* Contact Form */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Send className="h-5 w-5 mr-2" />
                Send us a Message
              </CardTitle>
              <CardDescription>
                Fill out the form below and we'll get back to you as soon as possible
              </CardDescription>
            </CardHeader>
            <CardContent>
              {isSubmitted ? (
                <div className="text-center py-8">
                  <CheckCircle className="h-12 w-12 text-green-600 mx-auto mb-4" />
                  <h3 className="text-xl font-bold mb-2">Message Sent!</h3>
                  <p className="text-slate-600 dark:text-slate-400 mb-4">
                    Thank you for contacting us. We'll get back to you within 24 hours.
                  </p>
                  <Button onClick={() => setIsSubmitted(false)} variant="outline">
                    Send Another Message
                  </Button>
                </div>
              ) : (
                <form onSubmit={handleSubmit} className="space-y-6">
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="name">Name *</Label>
                      <Input
                        id="name"
                        value={formData.name}
                        onChange={(e) => handleInputChange('name', e.target.value)}
                        placeholder="Your full name"
                        required
                      />
                    </div>
                    <div>
                      <Label htmlFor="email">Email *</Label>
                      <Input
                        id="email"
                        type="email"
                        value={formData.email}
                        onChange={(e) => handleInputChange('email', e.target.value)}
                        placeholder="your@email.com"
                        required
                      />
                    </div>
                  </div>
                  
                  <div className="grid md:grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="company">Company</Label>
                      <Input
                        id="company"
                        value={formData.company}
                        onChange={(e) => handleInputChange('company', e.target.value)}
                        placeholder="Your company name"
                      />
                    </div>
                    <div>
                      <Label htmlFor="role">Role</Label>
                      <Input
                        id="role"
                        value={formData.role}
                        onChange={(e) => handleInputChange('role', e.target.value)}
                        placeholder="Your job title"
                      />
                    </div>
                  </div>

                  <div>
                    <Label htmlFor="inquiry-type">Type of Inquiry</Label>
                    <Select onValueChange={(value) => handleInputChange('inquiryType', value)}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select inquiry type" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="sales">Sales & Pricing</SelectItem>
                        <SelectItem value="support">Technical Support</SelectItem>
                        <SelectItem value="partnership">Partnership</SelectItem>
                        <SelectItem value="security">Security & Compliance</SelectItem>
                        <SelectItem value="media">Media & Press</SelectItem>
                        <SelectItem value="careers">Careers</SelectItem>
                        <SelectItem value="feedback">Feedback</SelectItem>
                        <SelectItem value="other">Other</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="subject">Subject *</Label>
                    <Input
                      id="subject"
                      value={formData.subject}
                      onChange={(e) => handleInputChange('subject', e.target.value)}
                      placeholder="Brief description of your inquiry"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="message">Message *</Label>
                    <Textarea
                      id="message"
                      value={formData.message}
                      onChange={(e) => handleInputChange('message', e.target.value)}
                      placeholder="Tell us more about how we can help you..."
                      rows={6}
                      required
                    />
                  </div>

                  <Button 
                    type="submit" 
                    className="w-full" 
                    disabled={isSubmitting}
                  >
                    {isSubmitting ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                        Sending...
                      </>
                    ) : (
                      <>
                        <Send className="h-4 w-4 mr-2" />
                        Send Message
                      </>
                    )}
                  </Button>

                  <p className="text-xs text-slate-500 text-center">
                    By submitting this form, you agree to our Privacy Policy and Terms of Service.
                  </p>
                </form>
              )}
            </CardContent>
          </Card>

          {/* Support Channels */}
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Headphones className="h-5 w-5 mr-2" />
                  Other Ways to Reach Us
                </CardTitle>
                <CardDescription>
                  Choose the method that works best for you
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {supportChannels.map((channel) => (
                  <div key={channel.name} className="flex items-center justify-between p-4 border rounded-lg hover:bg-slate-50 dark:hover:bg-slate-800/50">
                    <div className="flex items-center space-x-3">
                      <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg">
                        <channel.icon className="h-5 w-5 text-blue-600" />
                      </div>
                      <div>
                        <h4 className="font-medium">{channel.name}</h4>
                        <p className="text-sm text-slate-600 dark:text-slate-400">{channel.description}</p>
                        <div className="flex items-center text-xs text-slate-500 mt-1">
                          <Clock className="h-3 w-3 mr-1" />
                          {channel.available}
                        </div>
                      </div>
                    </div>
                    <Button size="sm" variant="outline">
                      {channel.action}
                      <ArrowRight className="h-3 w-3 ml-1" />
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>

            {/* Emergency Contact */}
            <Alert className="bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800">
              <AlertCircle className="h-4 w-4 text-red-600" />
              <AlertDescription className="text-red-800 dark:text-red-200">
                <strong>Critical Issues or Security Incidents:</strong><br />
                For urgent production issues or security concerns, call our 24/7 hotline at{' '}
                <a href="tel:+15551234999" className="font-medium underline">+1 (555) 123-4999</a>
              </AlertDescription>
            </Alert>

            {/* Social Media */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center">
                  <Globe className="h-5 w-5 mr-2" />
                  Follow Us
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="flex space-x-4">
                  <Button variant="outline" size="sm" className="flex-1">
                    <Twitter className="h-4 w-4 mr-2" />
                    Twitter
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1">
                    <Linkedin className="h-4 w-4 mr-2" />
                    LinkedIn
                  </Button>
                  <Button variant="outline" size="sm" className="flex-1">
                    <Github className="h-4 w-4 mr-2" />
                    GitHub
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>

        {/* Office Locations */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Building className="h-7 w-7 mr-3" />
              Our Offices
            </CardTitle>
            <CardDescription>
              Visit us in person or reach out to your regional team
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              {officeLocations.map((office) => (
                <div key={office.name} className="border rounded-lg p-6 hover:shadow-md transition-shadow">
                  <h3 className="font-bold text-lg mb-3">{office.name}</h3>
                  <div className="space-y-3">
                    <div className="flex items-start">
                      <MapPin className="h-4 w-4 text-slate-500 mr-3 mt-1 flex-shrink-0" />
                      <div className="text-sm">
                        <div>{office.address}</div>
                        <div>{office.city}</div>
                        <div className="font-medium">{office.country}</div>
                      </div>
                    </div>
                    <div className="flex items-center">
                      <Phone className="h-4 w-4 text-slate-500 mr-3" />
                      <a href={`tel:${office.phone}`} className="text-sm text-blue-600 hover:underline">
                        {office.phone}
                      </a>
                    </div>
                    <div className="flex items-center">
                      <Globe className="h-4 w-4 text-slate-500 mr-3" />
                      <span className="text-sm">{office.timezone}</span>
                    </div>
                    <div className="flex items-center">
                      <Clock className="h-4 w-4 text-slate-500 mr-3" />
                      <span className="text-sm">{office.hours}</span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* FAQ Section */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <HelpCircle className="h-7 w-7 mr-3" />
              Frequently Asked Questions
            </CardTitle>
            <CardDescription>
              Quick answers to common questions
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-8">
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-2">What's your response time for support requests?</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Critical issues: Within 1 hour. General support: Within 4 hours during business hours. 
                    We offer 24/7 support for enterprise customers.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Do you offer phone support?</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Yes! Phone support is available for all paid plans. Free tier users can access 
                    our chat support and documentation.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Can I schedule a demo or consultation?</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Absolutely! Contact our sales team to schedule a personalized demo or 
                    technical consultation. We'll show you how CodeFlowOps can fit your workflow.
                  </p>
                </div>
              </div>
              
              <div className="space-y-6">
                <div>
                  <h4 className="font-semibold mb-2">How do I report a security vulnerability?</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Please email security@claydesk.com with details. We take security seriously 
                    and will respond within 24 hours to all vulnerability reports.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Do you have a status page?</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Yes! Check status.codeflowops.com for real-time service status, 
                    maintenance notifications, and incident reports.
                  </p>
                </div>
                
                <div>
                  <h4 className="font-semibold mb-2">Can you help with custom integrations?</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Our professional services team can help with custom integrations, 
                    migrations, and implementation. Contact sales for more information.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Partnership & Media */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <Card className="bg-gradient-to-br from-blue-50 to-indigo-100 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200">
            <CardContent className="p-8 text-center">
              <Rocket className="h-12 w-12 text-blue-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Partnership Opportunities</h3>
              <p className="text-slate-700 dark:text-slate-300 mb-4">
                Interested in partnering with us? We'd love to explore integration partnerships, 
                reseller opportunities, and technology alliances.
              </p>
              <Button className="bg-blue-600 hover:bg-blue-700">
                <Mail className="h-4 w-4 mr-2" />
                Contact Partnerships
              </Button>
            </CardContent>
          </Card>

          <Card className="bg-gradient-to-br from-purple-50 to-pink-100 dark:from-purple-900/20 dark:to-pink-900/20 border-purple-200">
            <CardContent className="p-8 text-center">
              <Volume2 className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h3 className="text-xl font-bold mb-2">Media & Press</h3>
              <p className="text-slate-700 dark:text-slate-300 mb-4">
                Journalists, bloggers, and content creators: we're happy to provide interviews, 
                expert commentary, and press materials.
              </p>
              <Button className="bg-purple-600 hover:bg-purple-700">
                <Image className="h-4 w-4 mr-2" />
                Press Inquiries
              </Button>
            </CardContent>
          </Card>
        </div>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            We're here to help! Whether you're just getting started or scaling to millions of users, 
            our team is ready to support your journey.
          </p>
          <p className="mt-2">
            For general inquiries: <a href="mailto:hello@codeflowops.com" className="text-blue-600 hover:underline">hello@codeflowops.com</a> • 
            For urgent issues: <a href="tel:+15551234999" className="text-blue-600 hover:underline ml-1">+1 (555) 123-4999</a>
          </p>
          <p className="mt-4 font-semibold">
            Thank you for choosing CodeFlowOps. We look forward to hearing from you!
          </p>
        </div>
      </div>
    </div>
  )
}
