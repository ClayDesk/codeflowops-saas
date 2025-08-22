'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Users2,
  ExternalLink,
  CheckCircle,
  Star,
  Globe,
  Building,
  Users,
  Zap,
  Shield,
  Code2,
  Cloud,
  Database,
  GitBranch,
  Settings,
  Rocket,
  Award,
  Target,
  TrendingUp,
  ArrowRight,
  Plus,
  Monitor,
  Smartphone,
  Server,
  Lock,
  Cpu,
  HardDrive,
  Network,
  Mail,
  Phone,
  MessageCircle,
  Calendar,
  FileText,
  Download,
  Play,
  Lightbulb,
  Heart,
  Puzzle,
  Link2,
  Workflow,
  Box,
  Package
} from 'lucide-react'

export default function PartnersPage() {
  const [activeTab, setActiveTab] = React.useState('technology')

  const technologyPartners = [
    {
      name: "Amazon Web Services",
      logo: "🛡️",
      category: "Cloud Infrastructure",
      tier: "Strategic",
      description: "Deep integration with AWS services including ECS, EKS, Lambda, and CloudFormation for seamless cloud deployments.",
      benefits: [
        "Native AWS service integration",
        "Auto-scaling and load balancing",
        "Cost optimization recommendations",
        "Security best practices"
      ],
      certifications: ["AWS Advanced Technology Partner", "AWS DevOps Competency"],
      integrations: ["EC2", "EKS", "Lambda", "CloudFormation", "RDS", "S3"],
      status: "Active",
      joinedDate: "2024",
      customerCount: "2,500+"
    },
    {
      name: "Microsoft Azure",
      logo: "☁️",
      category: "Cloud Platform",
      tier: "Strategic",
      description: "Comprehensive Azure integration supporting AKS, Azure DevOps, and Azure Resource Manager deployments.",
      benefits: [
        "Azure Kubernetes Service optimization",
        "DevOps pipeline integration",
        "Hybrid cloud deployments",
        "Enterprise security compliance"
      ],
      certifications: ["Microsoft Gold Partner", "Azure Expert MSP"],
      integrations: ["AKS", "Azure DevOps", "ARM Templates", "App Service", "SQL Database"],
      status: "Active",
      joinedDate: "2024",
      customerCount: "1,800+"
    },
    {
      name: "Google Cloud Platform",
      logo: "🌐",
      category: "Cloud Services",
      tier: "Strategic",
      description: "Full GCP integration with GKE, Cloud Run, and Google Cloud Build for modern application deployment.",
      benefits: [
        "GKE cluster management",
        "Serverless deployment options",
        "AI/ML workload optimization",
        "Multi-region deployments"
      ],
      certifications: ["Google Cloud Partner", "Infrastructure Specialization"],
      integrations: ["GKE", "Cloud Run", "Cloud Build", "Cloud Functions", "BigQuery"],
      status: "Active",
      joinedDate: "2024",
      customerCount: "1,200+"
    },
    {
      name: "Docker",
      logo: "🐳",
      category: "Containerization",
      tier: "Technology",
      description: "Native Docker integration for container building, scanning, and deployment across all environments.",
      benefits: [
        "Container image optimization",
        "Security vulnerability scanning",
        "Multi-architecture builds",
        "Registry integration"
      ],
      certifications: ["Docker Verified Publisher"],
      integrations: ["Docker Hub", "Docker Desktop", "Docker Compose", "Docker Swarm"],
      status: "Active",
      joinedDate: "2024",
      customerCount: "5,000+"
    },
    {
      name: "Kubernetes",
      logo: "⚙️",
      category: "Orchestration",
      tier: "Technology",
      description: "Deep Kubernetes integration supporting CNCF-compliant deployments across any K8s cluster.",
      benefits: [
        "Helm chart deployments",
        "Custom resource definitions",
        "RBAC and security policies",
        "Multi-cluster management"
      ],
      certifications: ["CNCF Member"],
      integrations: ["Helm", "Kubectl", "Kustomize", "Operators", "Service Mesh"],
      status: "Active",
      joinedDate: "2024",
      customerCount: "3,500+"
    },
    {
      name: "GitHub",
      logo: "🐙",
      category: "Source Control",
      tier: "Strategic",
      description: "Seamless GitHub integration with Actions, Packages, and Advanced Security for complete DevOps workflows.",
      benefits: [
        "GitHub Actions automation",
        "Package registry integration",
        "Security scanning",
        "Pull request deployments"
      ],
      certifications: ["GitHub Technology Partner"],
      integrations: ["GitHub Actions", "GitHub Packages", "GitHub Security", "GitHub API"],
      status: "Active",
      joinedDate: "2024",
      customerCount: "4,200+"
    }
  ]

  const integrationPartners = [
    {
      name: "Slack",
      logo: "💬",
      category: "Communication",
      description: "Real-time deployment notifications and team collaboration directly in Slack channels.",
      features: ["Deployment alerts", "Interactive approvals", "Team mentions", "Status updates"],
      setupTime: "5 minutes"
    },
    {
      name: "Jira",
      logo: "📋",
      category: "Project Management",
      description: "Automatic ticket updates and deployment tracking integrated with Jira workflows.",
      features: ["Auto ticket updates", "Deployment tracking", "Release notes", "Sprint reporting"],
      setupTime: "10 minutes"
    },
    {
      name: "PagerDuty",
      logo: "🚨",
      category: "Incident Management",
      description: "Intelligent alerting and incident response for deployment failures and system issues.",
      features: ["Smart alerting", "Escalation policies", "Incident correlation", "On-call scheduling"],
      setupTime: "15 minutes"
    },
    {
      name: "Datadog",
      logo: "📊",
      category: "Monitoring",
      description: "Advanced monitoring and observability for deployed applications and infrastructure.",
      features: ["APM integration", "Custom dashboards", "Alert correlation", "Performance insights"],
      setupTime: "20 minutes"
    },
    {
      name: "Terraform",
      logo: "🏗️",
      category: "Infrastructure",
      description: "Infrastructure as Code integration for managing cloud resources alongside applications.",
      features: ["State management", "Plan validation", "Resource tracking", "Compliance checks"],
      setupTime: "25 minutes"
    },
    {
      name: "Jenkins",
      logo: "🔧",
      category: "CI/CD",
      description: "Bridge existing Jenkins pipelines with CodeFlowOps deployment automation.",
      features: ["Pipeline migration", "Plugin compatibility", "Build integration", "Legacy support"],
      setupTime: "30 minutes"
    }
  ]

  const solutionPartners = [
    {
      name: "Acme DevOps Consulting",
      logo: "🏢",
      category: "Implementation",
      tier: "Gold",
      description: "Leading DevOps consultancy specializing in CodeFlowOps implementations for enterprise clients.",
      services: ["Implementation", "Training", "Custom Development", "24/7 Support"],
      expertise: ["Enterprise Architecture", "Cloud Migration", "DevOps Transformation"],
      certifications: ["CodeFlowOps Certified Partner", "Enterprise Implementation Specialist"],
      location: "Global",
      teamSize: "50+",
      projects: "200+",
      contact: "partners@acmedevops.com"
    },
    {
      name: "CloudScale Solutions",
      logo: "☁️",
      category: "Cloud Migration",
      tier: "Silver",
      description: "Cloud-first consultancy helping organizations migrate and optimize their deployment pipelines.",
      services: ["Cloud Migration", "Architecture Design", "Performance Optimization"],
      expertise: ["Multi-Cloud Strategy", "Kubernetes", "Microservices"],
      certifications: ["CodeFlowOps Certified", "AWS Solutions Architect"],
      location: "North America",
      teamSize: "25+",
      projects: "150+",
      contact: "hello@cloudscale.io"
    },
    {
      name: "DevSecOps Pro",
      logo: "🔒",
      category: "Security",
      tier: "Gold",
      description: "Security-focused partner specializing in secure deployment pipelines and compliance.",
      services: ["Security Audits", "Compliance Implementation", "Security Training"],
      expertise: ["DevSecOps", "Compliance", "Security Automation"],
      certifications: ["CodeFlowOps Security Specialist", "ISO 27001"],
      location: "Europe",
      teamSize: "30+",
      projects: "100+",
      contact: "security@devsecops-pro.com"
    }
  ]

  const partnerPrograms = [
    {
      name: "Technology Partner Program",
      icon: <Puzzle className="h-8 w-8" />,
      description: "For technology vendors looking to integrate with CodeFlowOps platform",
      benefits: [
        "Joint go-to-market opportunities",
        "Technical integration support",
        "Co-marketing programs",
        "Priority technical support",
        "Partner portal access",
        "Beta program participation"
      ],
      requirements: [
        "Technical integration capability",
        "Committed engineering resources",
        "Aligned product roadmap",
        "Marketing collaboration"
      ],
      applicationProcess: "Technical review → Integration development → Certification → Launch"
    },
    {
      name: "Solution Partner Program",
      icon: <Building className="h-8 w-8" />,
      description: "For consulting firms and system integrators implementing CodeFlowOps solutions",
      benefits: [
        "Sales and technical training",
        "Lead sharing programs",
        "Partner enablement resources",
        "Certification programs",
        "Marketing development funds",
        "Partner success manager"
      ],
      requirements: [
        "Proven implementation experience",
        "Certified team members",
        "Customer success focus",
        "Marketing investment"
      ],
      applicationProcess: "Application → Assessment → Training → Certification → Activation"
    },
    {
      name: "Marketplace Partner Program",
      icon: <Package className="h-8 w-8" />,
      description: "For vendors wanting to distribute solutions through CodeFlowOps marketplace",
      benefits: [
        "Global marketplace exposure",
        "Revenue sharing model",
        "Marketing amplification",
        "Customer analytics",
        "Payment processing",
        "Support infrastructure"
      ],
      requirements: [
        "Production-ready solution",
        "Quality assurance process",
        "Customer support capability",
        "Documentation standards"
      ],
      applicationProcess: "Submission → Review → Testing → Approval → Publication"
    }
  ]

  const successStories = [
    {
      partner: "AWS",
      customer: "TechCorp Inc.",
      industry: "Financial Services",
      challenge: "Needed to deploy microservices across multiple AWS regions with zero downtime",
      solution: "Implemented CodeFlowOps with AWS EKS and RDS for automated multi-region deployments",
      results: [
        "99.99% uptime achieved",
        "50% reduction in deployment time",
        "Zero failed deployments in 6 months",
        "Improved regulatory compliance"
      ],
      quote: "CodeFlowOps and AWS integration transformed our deployment process completely."
    },
    {
      partner: "Acme DevOps Consulting",
      customer: "Global Retail Chain",
      industry: "E-commerce",
      challenge: "Legacy deployment process causing frequent outages during peak shopping seasons",
      solution: "Complete DevOps transformation using CodeFlowOps with custom workflow automation",
      results: [
        "Zero outages during Black Friday",
        "10x faster feature delivery",
        "90% reduction in manual processes",
        "Improved team productivity"
      ],
      quote: "The partnership between CodeFlowOps and Acme DevOps delivered beyond our expectations."
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-7xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full shadow-lg">
              <Users2 className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Partner Ecosystem
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed mb-8">
            CodeFlowOps thrives through strategic partnerships that extend our platform's capabilities 
            and deliver exceptional value to our customers worldwide.
          </p>
          <div className="flex items-center justify-center space-x-8 text-sm text-slate-500">
            <div className="flex items-center">
              <Building className="h-4 w-4 mr-2" />
              <span>50+ Partners</span>
            </div>
            <div className="flex items-center">
              <Globe className="h-4 w-4 mr-2" />
              <span>Global Coverage</span>
            </div>
            <div className="flex items-center">
              <Award className="h-4 w-4 mr-2" />
              <span>Certified Integrations</span>
            </div>
          </div>
        </div>

        {/* Partner Categories Navigation */}
        <Card className="mb-12">
          <CardContent className="p-6">
            <div className="flex flex-wrap justify-center gap-4">
              <Button
                variant={activeTab === 'technology' ? 'default' : 'outline'}
                onClick={() => setActiveTab('technology')}
                className="flex items-center gap-2"
              >
                <Cpu className="h-4 w-4" />
                Technology Partners
              </Button>
              <Button
                variant={activeTab === 'integrations' ? 'default' : 'outline'}
                onClick={() => setActiveTab('integrations')}
                className="flex items-center gap-2"
              >
                <Link2 className="h-4 w-4" />
                Integrations
              </Button>
              <Button
                variant={activeTab === 'solutions' ? 'default' : 'outline'}
                onClick={() => setActiveTab('solutions')}
                className="flex items-center gap-2"
              >
                <Users className="h-4 w-4" />
                Solution Partners
              </Button>
              <Button
                variant={activeTab === 'programs' ? 'default' : 'outline'}
                onClick={() => setActiveTab('programs')}
                className="flex items-center gap-2"
              >
                <Rocket className="h-4 w-4" />
                Partner Programs
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Technology Partners */}
        {activeTab === 'technology' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Technology Partners
              </h2>
              <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                Strategic partnerships with leading technology providers that power the CodeFlowOps platform
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {technologyPartners.map((partner) => (
                <Card key={partner.name} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-3xl">{partner.logo}</div>
                        <div>
                          <CardTitle className="text-lg">{partner.name}</CardTitle>
                          <CardDescription>{partner.category}</CardDescription>
                        </div>
                      </div>
                      <Badge variant={partner.tier === 'Strategic' ? 'default' : 'secondary'}>
                        {partner.tier}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {partner.description}
                    </p>
                    
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Key Benefits:</h4>
                      <ul className="text-xs space-y-1">
                        {partner.benefits.map((benefit, idx) => (
                          <li key={idx} className="flex items-center">
                            <CheckCircle className="h-3 w-3 text-green-600 mr-2 flex-shrink-0" />
                            {benefit}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold text-sm mb-2">Integrations:</h4>
                      <div className="flex flex-wrap gap-1">
                        {partner.integrations.slice(0, 4).map((integration) => (
                          <Badge key={integration} variant="outline" className="text-xs">
                            {integration}
                          </Badge>
                        ))}
                        {partner.integrations.length > 4 && (
                          <Badge variant="outline" className="text-xs">
                            +{partner.integrations.length - 4} more
                          </Badge>
                        )}
                      </div>
                    </div>

                    <div className="pt-4 border-t">
                      <div className="flex items-center justify-between text-xs text-slate-500">
                        <span>{partner.customerCount} customers</span>
                        <span>Since {partner.joinedDate}</span>
                      </div>
                    </div>

                    <Button className="w-full" variant="outline">
                      <ExternalLink className="h-4 w-4 mr-2" />
                      View Integration
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Integrations */}
        {activeTab === 'integrations' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Platform Integrations
              </h2>
              <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                Connect CodeFlowOps with your existing tools and workflows for a seamless DevOps experience
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {integrationPartners.map((integration) => (
                <Card key={integration.name} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center gap-3 mb-4">
                      <div className="text-3xl">{integration.logo}</div>
                      <div>
                        <CardTitle className="text-lg">{integration.name}</CardTitle>
                        <CardDescription>{integration.category}</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {integration.description}
                    </p>
                    
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Features:</h4>
                      <ul className="text-xs space-y-1">
                        {integration.features.map((feature, idx) => (
                          <li key={idx} className="flex items-center">
                            <Zap className="h-3 w-3 text-blue-600 mr-2 flex-shrink-0" />
                            {feature}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-500">Setup time:</span>
                      <Badge variant="outline">{integration.setupTime}</Badge>
                    </div>

                    <div className="flex gap-2">
                      <Button className="flex-1" variant="outline">
                        <Settings className="h-4 w-4 mr-2" />
                        Setup
                      </Button>
                      <Button variant="outline">
                        <FileText className="h-4 w-4" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/20 dark:to-blue-900/20">
              <CardContent className="p-8 text-center">
                <h3 className="text-2xl font-bold mb-4">Can't find your tool?</h3>
                <p className="text-slate-600 dark:text-slate-400 mb-6">
                  We're constantly adding new integrations. Request your favorite tool or build a custom integration using our API.
                </p>
                <div className="flex flex-col sm:flex-row justify-center gap-4">
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Request Integration
                  </Button>
                  <Button variant="outline">
                    <Code2 className="h-4 w-4 mr-2" />
                    API Documentation
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Solution Partners */}
        {activeTab === 'solutions' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Solution Partners
              </h2>
              <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                Certified consultants and system integrators helping organizations maximize their CodeFlowOps investment
              </p>
            </div>

            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {solutionPartners.map((partner) => (
                <Card key={partner.name} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center gap-3">
                        <div className="text-3xl">{partner.logo}</div>
                        <div>
                          <CardTitle className="text-lg">{partner.name}</CardTitle>
                          <CardDescription>{partner.category}</CardDescription>
                        </div>
                      </div>
                      <Badge variant={partner.tier === 'Gold' ? 'default' : 'secondary'}>
                        {partner.tier}
                      </Badge>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    <p className="text-sm text-slate-600 dark:text-slate-400">
                      {partner.description}
                    </p>
                    
                    <div>
                      <h4 className="font-semibold text-sm mb-2">Services:</h4>
                      <div className="flex flex-wrap gap-1">
                        {partner.services.map((service) => (
                          <Badge key={service} variant="outline" className="text-xs">
                            {service}
                          </Badge>
                        ))}
                      </div>
                    </div>

                    <div>
                      <h4 className="font-semibold text-sm mb-2">Expertise:</h4>
                      <ul className="text-xs space-y-1">
                        {partner.expertise.map((skill, idx) => (
                          <li key={idx} className="flex items-center">
                            <Star className="h-3 w-3 text-yellow-500 mr-2 flex-shrink-0" />
                            {skill}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div className="grid grid-cols-2 gap-4 text-xs">
                      <div>
                        <span className="font-medium">Location:</span>
                        <div className="text-slate-600 dark:text-slate-400">{partner.location}</div>
                      </div>
                      <div>
                        <span className="font-medium">Team Size:</span>
                        <div className="text-slate-600 dark:text-slate-400">{partner.teamSize}</div>
                      </div>
                      <div>
                        <span className="font-medium">Projects:</span>
                        <div className="text-slate-600 dark:text-slate-400">{partner.projects}</div>
                      </div>
                      <div>
                        <span className="font-medium">Contact:</span>
                        <div className="text-blue-600 hover:underline cursor-pointer text-xs">
                          {partner.contact}
                        </div>
                      </div>
                    </div>

                    <Button className="w-full" variant="outline">
                      <Mail className="h-4 w-4 mr-2" />
                      Contact Partner
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}

        {/* Partner Programs */}
        {activeTab === 'programs' && (
          <div className="space-y-8">
            <div className="text-center mb-8">
              <h2 className="text-3xl font-bold text-slate-900 dark:text-slate-100 mb-4">
                Partner Programs
              </h2>
              <p className="text-lg text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                Join our partner ecosystem and grow your business with CodeFlowOps
              </p>
            </div>

            <div className="grid md:grid-cols-1 lg:grid-cols-3 gap-8">
              {partnerPrograms.map((program) => (
                <Card key={program.name} className="hover:shadow-lg transition-shadow">
                  <CardHeader className="text-center">
                    <div className="flex justify-center mb-4 text-blue-600">
                      {program.icon}
                    </div>
                    <CardTitle className="text-xl">{program.name}</CardTitle>
                    <CardDescription className="text-center">
                      {program.description}
                    </CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-6">
                    <div>
                      <h4 className="font-semibold text-sm mb-3">Benefits:</h4>
                      <ul className="text-sm space-y-2">
                        {program.benefits.map((benefit, idx) => (
                          <li key={idx} className="flex items-start">
                            <CheckCircle className="h-4 w-4 text-green-600 mr-2 flex-shrink-0 mt-0.5" />
                            {benefit}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold text-sm mb-3">Requirements:</h4>
                      <ul className="text-sm space-y-2">
                        {program.requirements.map((req, idx) => (
                          <li key={idx} className="flex items-start">
                            <Target className="h-4 w-4 text-blue-600 mr-2 flex-shrink-0 mt-0.5" />
                            {req}
                          </li>
                        ))}
                      </ul>
                    </div>

                    <div>
                      <h4 className="font-semibold text-sm mb-3">Application Process:</h4>
                      <p className="text-sm text-slate-600 dark:text-slate-400">
                        {program.applicationProcess}
                      </p>
                    </div>

                    <Button className="w-full">
                      <ArrowRight className="h-4 w-4 mr-2" />
                      Apply Now
                    </Button>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="bg-gradient-to-r from-purple-50 to-pink-50 dark:from-purple-900/20 dark:to-pink-900/20">
              <CardContent className="p-8">
                <div className="text-center mb-6">
                  <h3 className="text-2xl font-bold mb-4">Ready to Partner with Us?</h3>
                  <p className="text-slate-600 dark:text-slate-400 max-w-2xl mx-auto">
                    Join our growing partner ecosystem and help customers achieve their DevOps goals while growing your business.
                  </p>
                </div>
                <div className="flex flex-col sm:flex-row justify-center gap-4">
                  <Button size="lg">
                    <Users2 className="h-5 w-5 mr-2" />
                    Become a Partner
                  </Button>
                  <Button size="lg" variant="outline">
                    <Calendar className="h-5 w-5 mr-2" />
                    Schedule a Call
                  </Button>
                  <Button size="lg" variant="outline">
                    <Download className="h-5 w-5 mr-2" />
                    Partner Kit
                  </Button>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Success Stories */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <TrendingUp className="h-7 w-7 mr-3" />
              Partner Success Stories
            </CardTitle>
            <CardDescription>
              Real results from our partner collaborations
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-8">
              {successStories.map((story, idx) => (
                <div key={idx} className="border rounded-lg p-6">
                  <div className="flex items-center gap-2 mb-4">
                    <Badge variant="outline">{story.partner}</Badge>
                    <Badge variant="secondary">{story.industry}</Badge>
                  </div>
                  
                  <h4 className="font-semibold text-lg mb-2">{story.customer}</h4>
                  
                  <div className="space-y-4">
                    <div>
                      <h5 className="font-medium text-sm text-slate-600 dark:text-slate-400 mb-1">Challenge:</h5>
                      <p className="text-sm">{story.challenge}</p>
                    </div>
                    
                    <div>
                      <h5 className="font-medium text-sm text-slate-600 dark:text-slate-400 mb-1">Solution:</h5>
                      <p className="text-sm">{story.solution}</p>
                    </div>
                    
                    <div>
                      <h5 className="font-medium text-sm text-slate-600 dark:text-slate-400 mb-2">Results:</h5>
                      <ul className="text-sm space-y-1">
                        {story.results.map((result, resultIdx) => (
                          <li key={resultIdx} className="flex items-center">
                            <CheckCircle className="h-3 w-3 text-green-600 mr-2 flex-shrink-0" />
                            {result}
                          </li>
                        ))}
                      </ul>
                    </div>
                    
                    <blockquote className="border-l-4 border-blue-500 pl-4 italic text-sm text-slate-600 dark:text-slate-400">
                      "{story.quote}"
                    </blockquote>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Partner Contact */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Mail className="h-7 w-7 mr-3" />
              Partner Support
            </CardTitle>
            <CardDescription>
              Get in touch with our partner team
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-8">
              <div className="text-center">
                <div className="w-12 h-12 bg-blue-100 dark:bg-blue-900/30 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Mail className="h-6 w-6 text-blue-600" />
                </div>
                <h4 className="font-semibold mb-2">General Inquiries</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  Questions about our partner programs
                </p>
                <a href="mailto:partners@codeflowops.com" className="text-blue-600 hover:underline text-sm">
                  partners@codeflowops.com
                </a>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-green-100 dark:bg-green-900/30 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <Phone className="h-6 w-6 text-green-600" />
                </div>
                <h4 className="font-semibold mb-2">Technical Support</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  Integration and technical assistance
                </p>
                <a href="tel:+1-800-CODEFLOW" className="text-blue-600 hover:underline text-sm">
                  +1 (800) CODE-FLOW
                </a>
              </div>
              
              <div className="text-center">
                <div className="w-12 h-12 bg-purple-100 dark:bg-purple-900/30 rounded-lg flex items-center justify-center mx-auto mb-4">
                  <MessageCircle className="h-6 w-6 text-purple-600" />
                </div>
                <h4 className="font-semibold mb-2">Partner Chat</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                  Real-time chat support for partners
                </p>
                <Button size="sm" variant="outline">
                  <MessageCircle className="h-4 w-4 mr-2" />
                  Start Chat
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            Interested in partnering with CodeFlowOps? We'd love to hear from you.
          </p>
          <p className="mt-2">
            Contact our partner team: <a href="mailto:partners@codeflowops.com" className="text-blue-600 hover:underline">partners@codeflowops.com</a>
          </p>
          <p className="mt-4 font-semibold">
            © 2025 CodeFlowOps. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}
