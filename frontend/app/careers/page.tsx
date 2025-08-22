'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Users, 
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
  Coffee,
  Clock,
  TrendingUp,
  Cpu,
  Database,
  CloudCog,
  Sparkles,
  GraduationCap,
  Home,
  Plane,
  DollarSign,
  Plus,
  Search,
  Filter,
  ExternalLink,
  Briefcase,
  Timer,
  Target,
  BookOpen,
  Headphones,
  PieChart,
  Palette,
  Settings,
  Monitor,
  Smartphone,
  Network,
  Bug,
  Lock,
  FileText,
  BarChart3,
  MessageSquare,
  Camera,
  Megaphone
} from 'lucide-react'

const jobOpenings = [
  {
    id: 1,
    title: "Senior Full-Stack Engineer",
    department: "Engineering",
    location: "Remote (US/Canada)",
    type: "Full-time",
    experience: "5+ years",
    description: "Build and scale our AI-powered deployment platform using React, Node.js, and AWS.",
    skills: ["React", "TypeScript", "Node.js", "AWS", "Docker", "Kubernetes"],
    urgent: true
  },
  {
    id: 2,
    title: "DevOps Platform Engineer",
    department: "Engineering",
    location: "Remote",
    type: "Full-time",
    experience: "4+ years",
    description: "Design and implement scalable infrastructure automation and deployment pipelines.",
    skills: ["AWS", "Terraform", "Kubernetes", "Python", "CI/CD", "Monitoring"],
    urgent: false
  },
  {
    id: 3,
    title: "AI/ML Engineer",
    department: "Engineering",
    location: "Remote",
    type: "Full-time",
    experience: "3+ years",
    description: "Develop machine learning models for deployment optimization and predictive scaling.",
    skills: ["Python", "TensorFlow", "PyTorch", "MLOps", "AWS SageMaker", "Docker"],
    urgent: true
  },
  {
    id: 4,
    title: "Product Designer",
    department: "Design",
    location: "Remote",
    type: "Full-time",
    experience: "4+ years",
    description: "Shape the user experience of our developer tools and create intuitive interfaces.",
    skills: ["Figma", "User Research", "Prototyping", "Design Systems", "React", "CSS"],
    urgent: false
  },
  {
    id: 5,
    title: "Customer Success Manager",
    department: "Customer Success",
    location: "Remote (US)",
    type: "Full-time",
    experience: "3+ years",
    description: "Help enterprise customers maximize value from our platform and drive adoption.",
    skills: ["Customer Success", "SaaS", "Technical Communication", "Data Analysis"],
    urgent: false
  },
  {
    id: 6,
    title: "Security Engineer",
    department: "Security",
    location: "Remote",
    type: "Full-time",
    experience: "5+ years",
    description: "Ensure our platform meets the highest security standards and compliance requirements.",
    skills: ["Security", "AWS", "Penetration Testing", "Compliance", "Python", "Go"],
    urgent: false
  },
  {
    id: 7,
    title: "Technical Writer",
    department: "Developer Experience",
    location: "Remote",
    type: "Full-time",
    experience: "3+ years",
    description: "Create comprehensive documentation, tutorials, and guides for our developer community.",
    skills: ["Technical Writing", "API Documentation", "Developer Tools", "Git", "Markdown"],
    urgent: false
  },
  {
    id: 8,
    title: "Sales Engineer",
    department: "Sales",
    location: "Remote (US)",
    type: "Full-time",
    experience: "4+ years",
    description: "Support enterprise sales with technical expertise and solution demonstrations.",
    skills: ["Technical Sales", "DevOps", "Cloud Platforms", "Presentation", "Customer Facing"],
    urgent: false
  }
]

const benefits = [
  {
    category: "Health & Wellness",
    icon: Heart,
    items: [
      "100% covered health, dental, and vision insurance",
      "Mental health support and counseling services",
      "Annual wellness stipend ($1,500)",
      "Gym membership reimbursement",
      "Flexible sick leave and mental health days"
    ]
  },
  {
    category: "Work-Life Balance",
    icon: Home,
    items: [
      "Fully remote-first company culture",
      "Flexible working hours across time zones",
      "Unlimited PTO policy",
      "4-day work week (32 hours) in summer",
      "No-meeting Fridays"
    ]
  },
  {
    category: "Professional Growth",
    icon: GraduationCap,
    items: [
      "Annual learning budget ($3,000 per person)",
      "Conference attendance and speaking opportunities",
      "Internal tech talks and knowledge sharing",
      "Mentorship and career development programs",
      "Open source contribution time (20%)"
    ]
  },
  {
    category: "Financial Benefits",
    icon: DollarSign,
    items: [
      "Competitive salary with equity packages",
      "Annual performance bonuses",
      "401(k) with 6% company matching",
      "Stock option program for all employees",
      "Annual salary reviews and adjustments"
    ]
  },
  {
    category: "Equipment & Setup",
    icon: Monitor,
    items: [
      "MacBook Pro or high-end laptop of choice",
      "External monitor, keyboard, and mouse",
      "Ergonomic office chair allowance ($800)",
      "Home office setup budget ($2,000)",
      "Annual equipment refresh program"
    ]
  },
  {
    category: "Perks & Culture",
    icon: Coffee,
    items: [
      "Annual team retreats and offsites",
      "Monthly team building activities",
      "Coffee and snacks delivery program",
      "Pet-friendly video calls policy",
      "Sabbatical program (after 5 years)"
    ]
  }
]

const cultureValues = [
  {
    title: "Remote-First Culture",
    description: "We've been remote since day one. Our processes, tools, and culture are built around distributed collaboration.",
    icon: Globe
  },
  {
    title: "Continuous Learning",
    description: "Technology evolves fast, and so do we. We invest heavily in learning and professional development.",
    icon: BookOpen
  },
  {
    title: "Ownership Mindset",
    description: "Everyone owns their work and has the autonomy to make decisions. We trust our team to do great work.",
    icon: Target
  },
  {
    title: "Inclusive Environment",
    description: "We celebrate diversity and create an environment where everyone can bring their authentic self to work.",
    icon: Users
  },
  {
    title: "Work-Life Integration",
    description: "We believe in sustainable productivity. Great work happens when people are happy and well-rested.",
    icon: Heart
  },
  {
    title: "Innovation Focus",
    description: "We encourage experimentation and aren't afraid to fail fast. Innovation is part of our DNA.",
    icon: Lightbulb
  }
]

export default function CareersPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-purple-500 to-pink-600 rounded-full shadow-lg">
              <Users className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Join Our Team
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed mb-6">
            Help us build the future of software deployment. Work with cutting-edge technology, 
            solve challenging problems, and make an impact on developers worldwide.
          </p>
          <div className="flex items-center justify-center space-x-6 text-sm text-slate-500">
            <div className="flex items-center">
              <Users className="h-4 w-4 mr-2" />
              <span>50+ Team Members</span>
            </div>
            <div className="flex items-center">
              <Globe className="h-4 w-4 mr-2" />
              <span>100% Remote</span>
            </div>
            <div className="flex items-center">
              <Star className="h-4 w-4 mr-2" />
              <span>4.9/5 Employee Rating</span>
            </div>
          </div>
        </div>

        {/* Why Join Us */}
        <Card className="mb-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
          <CardContent className="p-8">
            <h2 className="text-3xl font-bold mb-6 text-center">Why CodeFlowOps?</h2>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="text-center">
                <Rocket className="h-12 w-12 mx-auto mb-4 text-blue-100" />
                <h3 className="font-bold text-lg mb-2">Cutting-Edge Technology</h3>
                <p className="text-blue-100">
                  Work with the latest AI, cloud technologies, and developer tools. 
                  Push the boundaries of what's possible in DevOps.
                </p>
              </div>
              <div className="text-center">
                <Heart className="h-12 w-12 mx-auto mb-4 text-blue-100" />
                <h3 className="font-bold text-lg mb-2">People-First Culture</h3>
                <p className="text-blue-100">
                  We prioritize your growth, well-being, and work-life balance. 
                  Join a team that truly cares about each other.
                </p>
              </div>
              <div className="text-center">
                <TrendingUp className="h-12 w-12 mx-auto mb-4 text-blue-100" />
                <h3 className="font-bold text-lg mb-2">High Impact Work</h3>
                <p className="text-blue-100">
                  Your work directly impacts thousands of developers and shapes 
                  the future of software deployment worldwide.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Open Positions */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Briefcase className="h-7 w-7 mr-3" />
              Open Positions
            </CardTitle>
            <CardDescription>
              Join us in building the future of DevOps automation
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {jobOpenings.map((job) => (
                <Card key={job.id} className="hover:shadow-lg transition-shadow">
                  <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center justify-between mb-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3 mb-2">
                          <h3 className="text-xl font-bold">{job.title}</h3>
                          {job.urgent && (
                            <Badge className="bg-red-100 text-red-800 text-xs">
                              <Zap className="h-3 w-3 mr-1" />
                              Urgent
                            </Badge>
                          )}
                        </div>
                        <div className="flex flex-wrap items-center gap-4 text-sm text-slate-600 dark:text-slate-400 mb-3">
                          <div className="flex items-center">
                            <Building className="h-4 w-4 mr-1" />
                            <span>{job.department}</span>
                          </div>
                          <div className="flex items-center">
                            <MapPin className="h-4 w-4 mr-1" />
                            <span>{job.location}</span>
                          </div>
                          <div className="flex items-center">
                            <Clock className="h-4 w-4 mr-1" />
                            <span>{job.type}</span>
                          </div>
                          <div className="flex items-center">
                            <GraduationCap className="h-4 w-4 mr-1" />
                            <span>{job.experience}</span>
                          </div>
                        </div>
                        <p className="text-slate-700 dark:text-slate-300 mb-4">
                          {job.description}
                        </p>
                        <div className="flex flex-wrap gap-2">
                          {job.skills.map((skill) => (
                            <Badge key={skill} variant="outline" className="text-xs">
                              {skill}
                            </Badge>
                          ))}
                        </div>
                      </div>
                      <div className="mt-4 md:mt-0 md:ml-6">
                        <Button className="w-full md:w-auto">
                          Apply Now
                          <ArrowRight className="h-4 w-4 ml-2" />
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
            <div className="mt-8 text-center">
              <Alert className="bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
                <Lightbulb className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800 dark:text-blue-200">
                  <strong>Don't see a perfect fit?</strong> We're always looking for talented people. 
                  Send us your resume at <a href="mailto:careers@claydesk.com" className="font-medium underline">careers@claydesk.com</a>
                </AlertDescription>
              </Alert>
            </div>
          </CardContent>
        </Card>

        {/* Benefits & Perks */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Star className="h-7 w-7 mr-3" />
              Benefits & Perks
            </CardTitle>
            <CardDescription>
              Comprehensive benefits package designed for your success
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-8">
              {benefits.map((benefit) => (
                <div key={benefit.category}>
                  <div className="flex items-center mb-4">
                    <div className="p-2 bg-blue-100 dark:bg-blue-900/20 rounded-lg mr-3">
                      <benefit.icon className="h-6 w-6 text-blue-600" />
                    </div>
                    <h3 className="font-bold text-lg">{benefit.category}</h3>
                  </div>
                  <div className="space-y-2">
                    {benefit.items.map((item, index) => (
                      <div key={index} className="flex items-start">
                        <CheckCircle className="h-4 w-4 text-green-600 mr-3 mt-0.5 flex-shrink-0" />
                        <span className="text-sm text-slate-700 dark:text-slate-300">{item}</span>
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Company Culture */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Heart className="h-7 w-7 mr-3" />
              Our Culture & Values
            </CardTitle>
            <CardDescription>
              What makes CodeFlowOps a great place to work
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {cultureValues.map((value) => (
                <div key={value.title} className="text-center p-6 bg-gradient-to-b from-slate-50 to-slate-100 dark:from-slate-800/50 dark:to-slate-700/50 rounded-lg">
                  <value.icon className="h-12 w-12 text-purple-600 mx-auto mb-4" />
                  <h3 className="font-bold text-lg mb-2">{value.title}</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    {value.description}
                  </p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Hiring Process */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Target className="h-7 w-7 mr-3" />
              Our Hiring Process
            </CardTitle>
            <CardDescription>
              Transparent, efficient, and candidate-friendly
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-6">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-blue-600 font-bold">1</span>
                </div>
                <h3 className="font-bold mb-2">Application Review</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  We review your application and resume within 2-3 business days.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-green-600 font-bold">2</span>
                </div>
                <h3 className="font-bold mb-2">Phone/Video Screening</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  30-minute chat with our recruiting team to discuss the role and your background.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-purple-600 font-bold">3</span>
                </div>
                <h3 className="font-bold mb-2">Technical Interview</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Role-specific technical discussion or coding challenge with the team.
                </p>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-orange-100 dark:bg-orange-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                  <span className="text-orange-600 font-bold">4</span>
                </div>
                <h3 className="font-bold mb-2">Final Interview</h3>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Meet with leadership and potential teammates to ensure mutual fit.
                </p>
              </div>
            </div>
            
            <div className="mt-8 p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
              <div className="flex items-center mb-2">
                <Timer className="h-5 w-5 text-blue-600 mr-2" />
                <span className="font-medium">Timeline: Typically 1-2 weeks from application to decision</span>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400">
                We believe in a respectful, efficient process that values your time. 
                You'll receive feedback at every stage, regardless of the outcome.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Diversity & Inclusion */}
        <Card className="mb-12 bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/10 dark:to-pink-900/10 border-purple-200">
          <CardContent className="p-8">
            <div className="text-center">
              <Users className="h-12 w-12 text-purple-600 mx-auto mb-4" />
              <h2 className="text-2xl font-bold mb-4">Diversity & Inclusion</h2>
              <p className="text-lg text-slate-700 dark:text-slate-300 max-w-3xl mx-auto mb-6">
                We're committed to building a diverse, equitable, and inclusive workplace where everyone can thrive. 
                We believe that diverse perspectives make us stronger and help us build better products.
              </p>
              <div className="grid md:grid-cols-3 gap-6 text-center">
                <div>
                  <div className="text-2xl font-bold text-purple-600 mb-1">40%</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">Women in Leadership</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-600 mb-1">60%</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">Underrepresented Groups</div>
                </div>
                <div>
                  <div className="text-2xl font-bold text-purple-600 mb-1">15+</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">Countries Represented</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Employee Testimonials */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <MessageSquare className="h-7 w-7 mr-3" />
              What Our Team Says
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="p-6 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <p className="text-sm italic mb-4">
                  "The learning opportunities here are incredible. I've grown more in 6 months 
                  than I did in years at previous companies."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-blue-500 rounded-full flex items-center justify-center mr-3">
                    <span className="text-white font-bold text-sm">AR</span>
                  </div>
                  <div>
                    <div className="font-medium">Alex Rodriguez</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Senior Engineer</div>
                  </div>
                </div>
              </div>
              
              <div className="p-6 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <p className="text-sm italic mb-4">
                  "The work-life balance is amazing. I can be productive and still have time 
                  for my family and hobbies."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-green-500 rounded-full flex items-center justify-center mr-3">
                    <span className="text-white font-bold text-sm">JL</span>
                  </div>
                  <div>
                    <div className="font-medium">Jordan Liu</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">Product Designer</div>
                  </div>
                </div>
              </div>
              
              <div className="p-6 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <p className="text-sm italic mb-4">
                  "Everyone here genuinely cares about each other's success. 
                  It's the most supportive team I've ever worked with."
                </p>
                <div className="flex items-center">
                  <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center mr-3">
                    <span className="text-white font-bold text-sm">TP</span>
                  </div>
                  <div>
                    <div className="font-medium">Taylor Park</div>
                    <div className="text-xs text-slate-600 dark:text-slate-400">DevOps Engineer</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* FAQ */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <FileText className="h-7 w-7 mr-3" />
              Frequently Asked Questions
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-6">
              <div>
                <h4 className="font-semibold mb-2">Do you sponsor visas?</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Currently, we only hire in countries where we have legal entities (US, Canada, UK, Germany). 
                  We don't sponsor visas at this time but are exploring this for exceptional candidates.
                </p>
              </div>
              
              <Separator />
              
              <div>
                <h4 className="font-semibold mb-2">What's your remote work policy?</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  We're 100% remote and have been since day one. We have team members across multiple time zones 
                  and are experts at async communication and remote collaboration.
                </p>
              </div>
              
              <Separator />
              
              <div>
                <h4 className="font-semibold mb-2">Do you offer internships?</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Yes! We offer paid internships in engineering, design, and product management. 
                  Our interns work on real projects and often receive full-time offers.
                </p>
              </div>
              
              <Separator />
              
              <div>
                <h4 className="font-semibold mb-2">What's the equity compensation like?</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  All full-time employees receive equity as part of their compensation package. 
                  The amount varies by role and seniority, and we're transparent about equity during the interview process.
                </p>
              </div>
              
              <Separator />
              
              <div>
                <h4 className="font-semibold mb-2">How do you handle different time zones?</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  We have core overlap hours for team collaboration (9 AM - 12 PM PT) and rely heavily on 
                  async communication. Most of our processes are designed to work across time zones.
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Contact / Apply */}
        <Card className="mb-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
          <CardContent className="p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Ready to Join Us?</h2>
            <p className="text-xl mb-6 text-blue-100">
              Take the next step in your career and help us revolutionize software deployment.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button size="lg" variant="secondary" className="bg-white text-blue-600 hover:bg-blue-50">
                <Briefcase className="h-5 w-5 mr-2" />
                View All Openings
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                <Mail className="h-5 w-5 mr-2" />
                Email Us Your Resume
              </Button>
            </div>
            <div className="mt-6 text-sm text-blue-100">
              Questions? Contact our recruiting team at 
              <a href="mailto:careers@claydesk.com" className="font-medium underline ml-1">careers@claydesk.com</a>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            CodeFlowOps is an equal opportunity employer committed to diversity and inclusion.
          </p>
          <p className="mt-2">
            We do not discriminate based on race, religion, color, national origin, gender, sexual orientation, 
            age, marital status, veteran status, or disability status.
          </p>
          <p className="mt-4 font-semibold">
            Ready to build the future? We'd love to hear from you.
          </p>
        </div>
      </div>
    </div>
  )
}
