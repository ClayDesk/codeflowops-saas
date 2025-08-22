'use client'

import React from 'react'
import JSZip from 'jszip'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  Download, 
  ExternalLink, 
  Copy, 
  Check, 
  Calendar, 
  Users, 
  Building, 
  Globe, 
  Award, 
  TrendingUp, 
  Rocket, 
  Mail,
  FileText,
  Image,
  Camera,
  Video,
  Mic,
  Quote,
  Star,
  Target,
  Zap,
  Shield,
  Code,
  Heart,
  Lightbulb,
  Archive,
  Folder,
  Link,
  BookOpen,
  Newspaper,
  Briefcase,
  PieChart,
  BarChart3,
  Monitor,
  Smartphone,
  Palette,
  Eye,
  MousePointer,
  Play,
  Pause,
  Volume2,
  Info,
  Loader2
} from 'lucide-react'

export default function PressKitPage() {
  const [copiedText, setCopiedText] = React.useState<string | null>(null)
  const [isDownloadingZip, setIsDownloadingZip] = React.useState(false)
  const [zipProgress, setZipProgress] = React.useState('')

  const copyToClipboard = (text: string, label: string) => {
    navigator.clipboard.writeText(text)
    setCopiedText(label)
    setTimeout(() => setCopiedText(null), 2000)
  }

  const downloadSvgAsPng = async (svgPath: string, filename: string, width: number = 1920, height: number = 1080) => {
    try {
      // Create a new image element
      const img: HTMLImageElement = document.createElement('img')
      img.crossOrigin = 'anonymous'
      
      // Load the SVG
      const response = await fetch(svgPath)
      const svgText = await response.text()
      const svgBlob = new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' })
      const svgUrl = URL.createObjectURL(svgBlob)
      
      img.onload = () => {
        // Create canvas
        const canvas = document.createElement('canvas')
        const ctx = canvas.getContext('2d')
        
        canvas.width = width
        canvas.height = height
        
        // Draw the image on canvas
        ctx?.drawImage(img, 0, 0, width, height)
        
        // Convert to PNG and download
        canvas.toBlob((blob) => {
          if (blob) {
            const url = URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = `${filename}.png`
            document.body.appendChild(a)
            a.click()
            document.body.removeChild(a)
            URL.revokeObjectURL(url)
          }
        }, 'image/png')
        
        URL.revokeObjectURL(svgUrl)
      }
      
      img.src = svgUrl
    } catch (error) {
      console.error('Error downloading PNG:', error)
      // Fallback: direct download of SVG
      const a = document.createElement('a')
      a.href = svgPath
      a.download = `${filename}.svg`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    }
  }

  const downloadAllScreenshots = async () => {
    setIsDownloadingZip(true)
    setZipProgress('Initializing...')
    
    const screenshots = [
      { path: '/images/screenshots/dashboard-overview.svg', name: 'dashboard-overview', width: 1920, height: 1080 },
      { path: '/images/screenshots/deployment-wizard.svg', name: 'deployment-wizard', width: 1920, height: 1080 },
      { path: '/images/screenshots/analytics-dashboard.svg', name: 'analytics-dashboard', width: 1920, height: 1080 },
      { path: '/images/screenshots/multi-tenant-management.svg', name: 'multi-tenant-management', width: 1920, height: 1080 },
      { path: '/images/screenshots/mobile-interface.svg', name: 'mobile-interface', width: 390, height: 844 },
      { path: '/images/screenshots/code-integration.svg', name: 'code-integration', width: 1920, height: 1080 }
    ]

    try {
      const zip = new JSZip()
      const folder = zip.folder('codeflowops-screenshots')
      
      setZipProgress('Converting images...')
      
      // Convert each SVG to PNG and add to ZIP
      const promises = screenshots.map(async (screenshot, index) => {
        try {
          setZipProgress(`Processing ${screenshot.name}... (${index + 1}/${screenshots.length})`)
          
          // Load the SVG
          const response = await fetch(screenshot.path)
          const svgText = await response.text()
          const svgBlob = new Blob([svgText], { type: 'image/svg+xml;charset=utf-8' })
          const svgUrl = URL.createObjectURL(svgBlob)
          
          // Convert to PNG blob
          const pngBlob = await new Promise<Blob | null>((resolve, reject) => {
            const img: HTMLImageElement = document.createElement('img')
            img.crossOrigin = 'anonymous'
            
            img.onload = () => {
              try {
                const canvas = document.createElement('canvas')
                const ctx = canvas.getContext('2d')
                
                if (!ctx) {
                  resolve(null)
                  return
                }
                
                canvas.width = screenshot.width
                canvas.height = screenshot.height
                
                // Set white background for better PNG output
                ctx.fillStyle = '#ffffff'
                ctx.fillRect(0, 0, canvas.width, canvas.height)
                
                ctx.drawImage(img, 0, 0, screenshot.width, screenshot.height)
                
                canvas.toBlob((blob) => {
                  resolve(blob)
                }, 'image/png', 1.0)
                
                URL.revokeObjectURL(svgUrl)
              } catch (error) {
                console.error('Canvas error:', error)
                resolve(null)
              }
            }
            
            img.onerror = (error) => {
              console.error('Image load error:', error)
              resolve(null)
            }
            
            // Add a timeout
            setTimeout(() => {
              console.error('Image load timeout for:', screenshot.name)
              resolve(null)
            }, 10000)
            
            img.src = svgUrl
          })
          
          if (pngBlob && folder) {
            folder.file(`${screenshot.name}.png`, pngBlob)
            console.log(`Added ${screenshot.name}.png to ZIP`)
          } else {
            console.error(`Failed to convert ${screenshot.name} to PNG`)
          }
        } catch (error) {
          console.error(`Error processing ${screenshot.name}:`, error)
        }
      })
      
      // Wait for all conversions to complete
      await Promise.all(promises)
      
      // Check if we have any files in the ZIP
      const zipContents = Object.keys(folder?.files || {})
      if (zipContents.length === 0) {
        throw new Error('No files were successfully converted to PNG')
      }
      
      console.log(`ZIP contains ${zipContents.length} files:`, zipContents)
      setZipProgress('Creating ZIP file...')
      
      // Generate and download ZIP
      const zipBlob = await zip.generateAsync({ 
        type: 'blob',
        compression: 'DEFLATE',
        compressionOptions: {
          level: 6
        }
      })
      
      console.log('ZIP blob generated, size:', zipBlob.size)
      setZipProgress('Starting download...')
      
      const url = URL.createObjectURL(zipBlob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'codeflowops-screenshots.zip'
      a.style.display = 'none'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      
      // Clean up after a delay
      setTimeout(() => {
        URL.revokeObjectURL(url)
      }, 1000)
      
      console.log('ZIP download initiated')
      setZipProgress('Download started!')
      
    } catch (error) {
      console.error('Error creating ZIP file:', error)
      setZipProgress('Error occurred, trying individual downloads...')
      
      // Fallback to individual downloads
      for (let i = 0; i < screenshots.length; i++) {
        const screenshot = screenshots[i]
        setTimeout(() => {
          downloadSvgAsPng(screenshot.path, screenshot.name, screenshot.width, screenshot.height)
        }, i * 500)
      }
    } finally {
      setTimeout(() => {
        setIsDownloadingZip(false)
        setZipProgress('')
      }, 2000)
    }
  }

  const companyFacts = [
    { label: "Founded", value: "2024" },
    { label: "Headquarters", value: "Middletown, CT, USA" },
    { label: "Employees", value: "25-50" },
    { label: "Customers", value: "10,000+" },
    { label: "Deployments", value: "1M+ successful" },
    { label: "Countries", value: "50+" },
    { label: "Uptime", value: "99.9%" },
    { label: "Funding", value: "Series A" }
  ]

  const logoAssets = [
    {
      name: "Primary Logo",
      description: "Main CodeFlowOps logo for light backgrounds",
      formats: ["PNG", "SVG", "JPG"],
      sizes: ["512x512", "256x256", "128x128"],
      background: "Transparent/White"
    },
    {
      name: "Logo Dark",
      description: "CodeFlowOps logo optimized for dark backgrounds",
      formats: ["PNG", "SVG", "JPG"],
      sizes: ["512x512", "256x256", "128x128"],
      background: "Transparent/Dark"
    },
    {
      name: "Icon Only",
      description: "CodeFlowOps icon without text",
      formats: ["PNG", "SVG", "ICO"],
      sizes: ["512x512", "256x256", "128x128", "64x64", "32x32"],
      background: "Transparent"
    },
    {
      name: "Horizontal Logo",
      description: "Wide format logo for headers and banners",
      formats: ["PNG", "SVG", "JPG"],
      sizes: ["1200x400", "800x267", "600x200"],
      background: "Transparent/White"
    }
  ]

  const screenshots = [
    {
      name: "Dashboard Overview",
      description: "Main platform dashboard showing deployment pipeline",
      category: "Interface",
      size: "1920x1080"
    },
    {
      name: "Deployment Wizard",
      description: "Step-by-step deployment configuration interface",
      category: "Interface",
      size: "1920x1080"
    },
    {
      name: "Analytics Dashboard",
      description: "Real-time deployment analytics and metrics",
      category: "Interface",
      size: "1920x1080"
    },
    {
      name: "Multi-tenant Management",
      description: "Enterprise multi-tenant deployment management",
      category: "Interface",
      size: "1920x1080"
    },
    {
      name: "Mobile Interface",
      description: "CodeFlowOps mobile app interface",
      category: "Mobile",
      size: "375x812"
    },
    {
      name: "Code Integration",
      description: "GitHub integration and repository management",
      category: "Integration",
      size: "1920x1080"
    }
  ]

  const executiveBios = [
    {
      name: "Alex Kumar",
      title: "CEO & Co-Founder",
      bio: "Alex brings 15+ years of cloud infrastructure experience from Amazon Web Services, where he served as Principal Engineer. He led the development of several core AWS services and holds 12 patents in distributed systems. Alex is passionate about democratizing DevOps and making enterprise-grade deployment tools accessible to every developer.",
      expertise: ["Cloud Infrastructure", "Distributed Systems", "Product Strategy"],
      education: "MS Computer Science, Stanford University",
      previous: "Principal Engineer at AWS, Senior Engineer at Google"
    },
    {
      name: "Sarah Chen",
      title: "CTO & Co-Founder", 
      bio: "Dr. Chen is an AI/ML expert with a PhD in Computer Science from MIT. She previously worked at Google Brain, where she contributed to TensorFlow and led research in automated systems optimization. Sarah's vision for AI-powered DevOps automation drives CodeFlowOps' technical innovation.",
      expertise: ["Artificial Intelligence", "Machine Learning", "Systems Architecture"],
      education: "PhD Computer Science, MIT; BS Computer Science, UC Berkeley",
      previous: "Research Scientist at Google Brain, Software Engineer at Facebook"
    },
    {
      name: "Michael Rodriguez",
      title: "VP of Engineering",
      bio: "Michael is a seasoned engineering leader with expertise in microservices architecture and platform engineering. At Netflix, he led the team responsible for deployment infrastructure serving 200M+ users. He's known for building high-performing engineering teams and scalable systems.",
      expertise: ["Platform Engineering", "Microservices", "Team Leadership"],
      education: "BS Computer Engineering, Carnegie Mellon University",
      previous: "Staff Engineer at Netflix, Senior Engineer at Uber"
    }
  ]

  const keyMessages = [
    {
      title: "Mission Statement",
      content: "CodeFlowOps democratizes DevOps by providing intelligent, automated deployment solutions that eliminate complexity and accelerate innovation for developers worldwide."
    },
    {
      title: "Unique Value Proposition",
      content: "The first AI-powered deployment platform that understands your code, predicts infrastructure needs, and automates the entire deployment lifecycle—making enterprise-grade DevOps accessible to every developer."
    },
    {
      title: "Market Position",
      content: "CodeFlowOps is pioneering the next generation of deployment automation, combining artificial intelligence with proven DevOps practices to create the most intelligent deployment platform available."
    },
    {
      title: "Vision",
      content: "A world where deployment friction is eliminated, where great ideas become reality in minutes not months, and where developers can focus on building amazing products instead of wrestling with infrastructure."
    }
  ]

  const pressReleases = [
    {
      title: "CodeFlowOps Raises $15M Series A to Democratize AI-Powered DevOps",
      date: "August 15, 2025",
      summary: "Leading deployment automation platform secures Series A funding to accelerate product development and global expansion.",
      category: "Funding"
    },
    {
      title: "CodeFlowOps Launches Enterprise Multi-Tenant Deployment Platform",
      date: "July 22, 2025", 
      summary: "New enterprise features enable organizations to manage thousands of deployments across multiple environments with AI-powered optimization.",
      category: "Product"
    },
    {
      title: "CodeFlowOps Surpasses 1 Million Successful Deployments Milestone",
      date: "June 10, 2025",
      summary: "Platform growth accelerates as developers worldwide adopt AI-powered deployment automation, reducing deployment time by 75%.",
      category: "Milestone"
    },
    {
      title: "CodeFlowOps Partners with Leading Cloud Providers for Enhanced Integration",
      date: "May 5, 2025",
      summary: "Strategic partnerships with AWS, Google Cloud, and Azure expand deployment capabilities and improve user experience.",
      category: "Partnership"
    }
  ]

  const mediaKit = [
    {
      type: "Fact Sheet",
      description: "One-page company overview with key statistics and product information",
      format: "PDF",
      updated: "August 2025"
    },
    {
      type: "Executive Bios",
      description: "Detailed biographies of leadership team with high-resolution photos",
      format: "PDF + Images",
      updated: "August 2025"
    },
    {
      type: "Product Screenshots",
      description: "High-resolution screenshots of platform interface and features",
      format: "PNG/JPG",
      updated: "August 2025"
    },
    {
      type: "Logo Package",
      description: "Complete brand assets including logos, icons, and usage guidelines",
      format: "ZIP",
      updated: "August 2025"
    },
    {
      type: "Video Assets",
      description: "Product demo videos and executive interview footage",
      format: "MP4",
      updated: "July 2025"
    }
  ]

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-12">
          <div className="flex items-center justify-center mb-6">
            <div className="p-4 bg-gradient-to-br from-orange-500 to-red-600 rounded-full shadow-lg">
              <Newspaper className="h-12 w-12 text-white" />
            </div>
          </div>
          <h1 className="text-5xl font-bold text-slate-900 dark:text-slate-100 mb-4">
            Press Kit
          </h1>
          <p className="text-xl text-slate-600 dark:text-slate-400 max-w-3xl mx-auto leading-relaxed mb-6">
            Media resources, company information, and brand assets for journalists, 
            bloggers, and content creators covering CodeFlowOps.
          </p>
          <div className="flex items-center justify-center space-x-6 text-sm text-slate-500">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-2" />
              <span>Updated August 2025</span>
            </div>
            <div className="flex items-center">
              <Download className="h-4 w-4 mr-2" />
              <span>All Assets Available</span>
            </div>
            <div className="flex items-center">
              <Mail className="h-4 w-4 mr-2" />
              <span>press@codeflowops.com</span>
            </div>
          </div>
        </div>

        {/* Quick Download */}
        <Card className="mb-12 bg-gradient-to-r from-blue-500 to-purple-600 text-white">
          <CardContent className="p-8 text-center">
            <h2 className="text-3xl font-bold mb-4">Complete Press Kit</h2>
            <p className="text-xl mb-6 text-blue-100">
              Download our complete media package with all logos, screenshots, bios, and fact sheets.
            </p>
            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button size="lg" variant="secondary" className="bg-white text-blue-600 hover:bg-blue-50">
                <Download className="h-5 w-5 mr-2" />
                Download Full Kit (24 MB)
              </Button>
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white/10">
                <Eye className="h-5 w-5 mr-2" />
                Quick Fact Sheet
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Company Facts */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Building className="h-7 w-7 mr-3" />
              Company Facts & Figures
            </CardTitle>
            <CardDescription>
              Key statistics and information about CodeFlowOps
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-6">
              {companyFacts.map((fact) => (
                <div key={fact.label} className="text-center p-4 bg-slate-50 dark:bg-slate-800/50 rounded-lg">
                  <div className="text-2xl font-bold text-blue-600 mb-1">{fact.value}</div>
                  <div className="text-sm text-slate-600 dark:text-slate-400">{fact.label}</div>
                </div>
              ))}
            </div>
            
            <div className="mt-8 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
              <div className="flex items-center justify-between">
                <div className="text-sm font-medium">Copy Company Description:</div>
                <Button 
                  size="sm" 
                  variant="outline"
                  onClick={() => copyToClipboard(
                    "CodeFlowOps is the leading AI-powered deployment automation platform, helping developers and enterprises deploy code faster, safer, and smarter. Founded in 2024, the company serves over 10,000 developers worldwide with intelligent deployment solutions that eliminate complexity and accelerate innovation.",
                    "Company Description"
                  )}
                >
                  {copiedText === "Company Description" ? (
                    <>
                      <Check className="h-4 w-4 mr-2" />
                      Copied!
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4 mr-2" />
                      Copy
                    </>
                  )}
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Key Messages */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Quote className="h-7 w-7 mr-3" />
              Key Messages & Positioning
            </CardTitle>
            <CardDescription>
              Core messaging and value propositions
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {keyMessages.map((message) => (
              <div key={message.title} className="border rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <h4 className="font-semibold text-lg">{message.title}</h4>
                  <Button 
                    size="sm" 
                    variant="outline"
                    onClick={() => copyToClipboard(message.content, message.title)}
                  >
                    {copiedText === message.title ? (
                      <>
                        <Check className="h-4 w-4 mr-2" />
                        Copied!
                      </>
                    ) : (
                      <>
                        <Copy className="h-4 w-4 mr-2" />
                        Copy
                      </>
                    )}
                  </Button>
                </div>
                <p className="text-slate-700 dark:text-slate-300">{message.content}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Logo & Brand Assets */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Palette className="h-7 w-7 mr-3" />
              Logo & Brand Assets
            </CardTitle>
            <CardDescription>
              Official CodeFlowOps logos and brand guidelines
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-6">
              {logoAssets.map((asset) => (
                <div key={asset.name} className="border rounded-lg p-6">
                  <h4 className="font-semibold text-lg mb-2">{asset.name}</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{asset.description}</p>
                  
                  <div className="space-y-2 mb-4">
                    <div className="text-xs">
                      <span className="font-medium">Formats:</span> {asset.formats.join(", ")}
                    </div>
                    <div className="text-xs">
                      <span className="font-medium">Sizes:</span> {asset.sizes.join(", ")}
                    </div>
                    <div className="text-xs">
                      <span className="font-medium">Background:</span> {asset.background}
                    </div>
                  </div>
                  
                  <div className="flex gap-2">
                    <Button size="sm" variant="outline" className="flex-1">
                      <Download className="h-4 w-4 mr-2" />
                      Download
                    </Button>
                    <Button size="sm" variant="outline">
                      <Eye className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
            
            <Alert className="mt-6 bg-orange-50 border-orange-200 dark:bg-orange-900/20 dark:border-orange-800">
              <Info className="h-4 w-4 text-orange-600" />
              <AlertDescription className="text-orange-800 dark:text-orange-200">
                <strong>Usage Guidelines:</strong> Please maintain minimum clear space around logos, 
                don't modify colors or proportions, and ensure adequate contrast on backgrounds. 
                Full brand guidelines included in download package.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        {/* Screenshots */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Monitor className="h-7 w-7 mr-3" />
              Product Screenshots
            </CardTitle>
            <CardDescription>
              High-resolution screenshots of the CodeFlowOps platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              <div className="border rounded-lg p-4">
                <div className="aspect-video bg-slate-900 rounded-lg mb-4 overflow-hidden">
                  <img 
                    src="/images/screenshots/dashboard-overview.svg" 
                    alt="Dashboard Overview"
                    className="w-full h-full object-cover"
                  />
                </div>
                <h4 className="font-semibold mb-1">Dashboard Overview</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Main dashboard with deployment statistics and real-time activity</p>
                <div className="flex items-center justify-between text-xs">
                  <Badge variant="outline">Dashboard</Badge>
                  <span className="text-slate-500">1920x1080</span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="w-full mt-3"
                  onClick={() => downloadSvgAsPng('/images/screenshots/dashboard-overview.svg', 'dashboard-overview', 1920, 1080)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download PNG
                </Button>
              </div>

              <div className="border rounded-lg p-4">
                <div className="aspect-video bg-slate-900 rounded-lg mb-4 overflow-hidden">
                  <img 
                    src="/images/screenshots/deployment-wizard.svg" 
                    alt="Deployment Wizard"
                    className="w-full h-full object-cover"
                  />
                </div>
                <h4 className="font-semibold mb-1">Deployment Wizard</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Step-by-step deployment process with AI optimization</p>
                <div className="flex items-center justify-between text-xs">
                  <Badge variant="outline">Wizard</Badge>
                  <span className="text-slate-500">1920x1080</span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="w-full mt-3"
                  onClick={() => downloadSvgAsPng('/images/screenshots/deployment-wizard.svg', 'deployment-wizard', 1920, 1080)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download PNG
                </Button>
              </div>

              <div className="border rounded-lg p-4">
                <div className="aspect-video bg-slate-900 rounded-lg mb-4 overflow-hidden">
                  <img 
                    src="/images/screenshots/analytics-dashboard.svg" 
                    alt="Analytics Dashboard"
                    className="w-full h-full object-cover"
                  />
                </div>
                <h4 className="font-semibold mb-1">Analytics Dashboard</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Comprehensive analytics with deployment metrics and trends</p>
                <div className="flex items-center justify-between text-xs">
                  <Badge variant="outline">Analytics</Badge>
                  <span className="text-slate-500">1920x1080</span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="w-full mt-3"
                  onClick={() => downloadSvgAsPng('/images/screenshots/analytics-dashboard.svg', 'analytics-dashboard', 1920, 1080)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download PNG
                </Button>
              </div>

              <div className="border rounded-lg p-4">
                <div className="aspect-video bg-slate-900 rounded-lg mb-4 overflow-hidden">
                  <img 
                    src="/images/screenshots/multi-tenant-management.svg" 
                    alt="Multi-Tenant Management"
                    className="w-full h-full object-cover"
                  />
                </div>
                <h4 className="font-semibold mb-1">Multi-Tenant Management</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Enterprise tenant management with resource allocation</p>
                <div className="flex items-center justify-between text-xs">
                  <Badge variant="outline">Enterprise</Badge>
                  <span className="text-slate-500">1920x1080</span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="w-full mt-3"
                  onClick={() => downloadSvgAsPng('/images/screenshots/multi-tenant-management.svg', 'multi-tenant-management', 1920, 1080)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download PNG
                </Button>
              </div>

              <div className="border rounded-lg p-4">
                <div className="aspect-[9/16] bg-slate-900 rounded-lg mb-4 overflow-hidden max-w-32 mx-auto">
                  <img 
                    src="/images/screenshots/mobile-interface.svg" 
                    alt="Mobile Interface"
                    className="w-full h-full object-cover"
                  />
                </div>
                <h4 className="font-semibold mb-1">Mobile Interface</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">Mobile-optimized interface for deployment management</p>
                <div className="flex items-center justify-between text-xs">
                  <Badge variant="outline">Mobile</Badge>
                  <span className="text-slate-500">390x844</span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="w-full mt-3"
                  onClick={() => downloadSvgAsPng('/images/screenshots/mobile-interface.svg', 'mobile-interface', 390, 844)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download PNG
                </Button>
              </div>

              <div className="border rounded-lg p-4">
                <div className="aspect-video bg-slate-900 rounded-lg mb-4 overflow-hidden">
                  <img 
                    src="/images/screenshots/code-integration.svg" 
                    alt="Code Integration"
                    className="w-full h-full object-cover"
                  />
                </div>
                <h4 className="font-semibold mb-1">Code Integration</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">VS Code integration showing deployment workflow</p>
                <div className="flex items-center justify-between text-xs">
                  <Badge variant="outline">IDE</Badge>
                  <span className="text-slate-500">1920x1080</span>
                </div>
                <Button 
                  size="sm" 
                  variant="outline" 
                  className="w-full mt-3"
                  onClick={() => downloadSvgAsPng('/images/screenshots/code-integration.svg', 'code-integration', 1920, 1080)}
                >
                  <Download className="h-4 w-4 mr-2" />
                  Download PNG
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Bulk Download Options */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Archive className="h-7 w-7 mr-3" />
              Bulk Downloads
            </CardTitle>
            <CardDescription>
              Download multiple assets at once for convenience
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              <div className="border rounded-lg p-6">
                <h4 className="font-semibold text-lg mb-2">All Screenshots (ZIP)</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Download all 6 product screenshots in high-quality PNG format as a single ZIP file
                </p>
                <Button 
                  className="w-full" 
                  onClick={downloadAllScreenshots}
                  disabled={isDownloadingZip}
                >
                  {isDownloadingZip ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      {zipProgress || 'Creating ZIP...'}
                    </>
                  ) : (
                    <>
                      <Download className="h-4 w-4 mr-2" />
                      Download ZIP (6 files)
                    </>
                  )}
                </Button>
              </div>
              
              <div className="border rounded-lg p-6">
                <h4 className="font-semibold text-lg mb-2">Media Kit Package</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  Complete press kit with logos, screenshots, and brand guidelines
                </p>
                <Button className="w-full" variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Download ZIP
                </Button>
              </div>
              
              <div className="border rounded-lg p-6">
                <h4 className="font-semibold text-lg mb-2">Executive Photos</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                  High-resolution photos of leadership team members
                </p>
                <Button className="w-full" variant="outline">
                  <Download className="h-4 w-4 mr-2" />
                  Download ZIP
                </Button>
              </div>
            </div>
            
            <Alert className="mt-6 bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
              <Info className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-800 dark:text-blue-200">
                <strong>Note:</strong> The ZIP download will process all screenshots and create a single file. 
                This may take a few moments to complete. Individual downloads are also available above.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        {/* Executive Team */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Users className="h-7 w-7 mr-3" />
              Executive Team Bios
            </CardTitle>
            <CardDescription>
              Leadership team information and high-resolution photos
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-8">
            {executiveBios.map((exec) => (
              <div key={exec.name} className="border rounded-lg p-6">
                <div className="flex flex-col md:flex-row gap-6">
                  <div className="flex-shrink-0">
                    <div className="w-32 h-32 bg-gradient-to-br from-blue-500 to-purple-600 rounded-lg flex items-center justify-center">
                      <span className="text-white font-bold text-2xl">{exec.name.split(' ').map(n => n[0]).join('')}</span>
                    </div>
                    <Button size="sm" variant="outline" className="w-full mt-2">
                      <Download className="h-4 w-4 mr-2" />
                      Hi-Res Photo
                    </Button>
                  </div>
                  
                  <div className="flex-1">
                    <h3 className="text-xl font-bold mb-1">{exec.name}</h3>
                    <p className="text-blue-600 font-medium mb-3">{exec.title}</p>
                    <p className="text-slate-700 dark:text-slate-300 mb-4">{exec.bio}</p>
                    
                    <div className="grid md:grid-cols-3 gap-4 text-sm">
                      <div>
                        <span className="font-medium">Expertise:</span>
                        <div className="text-slate-600 dark:text-slate-400">{exec.expertise.join(", ")}</div>
                      </div>
                      <div>
                        <span className="font-medium">Education:</span>
                        <div className="text-slate-600 dark:text-slate-400">{exec.education}</div>
                      </div>
                      <div>
                        <span className="font-medium">Previous:</span>
                        <div className="text-slate-600 dark:text-slate-400">{exec.previous}</div>
                      </div>
                    </div>
                    
                    <Button 
                      size="sm" 
                      variant="outline" 
                      className="mt-4"
                      onClick={() => copyToClipboard(exec.bio, `${exec.name} Bio`)}
                    >
                      {copiedText === `${exec.name} Bio` ? (
                        <>
                          <Check className="h-4 w-4 mr-2" />
                          Copied!
                        </>
                      ) : (
                        <>
                          <Copy className="h-4 w-4 mr-2" />
                          Copy Bio
                        </>
                      )}
                    </Button>
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Recent Press Releases */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <FileText className="h-7 w-7 mr-3" />
              Recent Press Releases
            </CardTitle>
            <CardDescription>
              Latest company announcements and news
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {pressReleases.map((release) => (
                <div key={release.title} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                  <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h4 className="font-semibold text-lg">{release.title}</h4>
                        <Badge variant="outline">{release.category}</Badge>
                      </div>
                      <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">{release.summary}</p>
                      <div className="flex items-center text-xs text-slate-500">
                        <Calendar className="h-3 w-3 mr-1" />
                        {release.date}
                      </div>
                    </div>
                    <div className="flex gap-2">
                      <Button size="sm" variant="outline">
                        <Eye className="h-4 w-4 mr-2" />
                        Read
                      </Button>
                      <Button size="sm" variant="outline">
                        <Download className="h-4 w-4 mr-2" />
                        PDF
                      </Button>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Media Kit Downloads */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Archive className="h-7 w-7 mr-3" />
              Media Kit Downloads
            </CardTitle>
            <CardDescription>
              Organized packages for different media needs
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
              {mediaKit.map((kit) => (
                <div key={kit.type} className="border rounded-lg p-6 hover:shadow-md transition-shadow">
                  <h4 className="font-semibold text-lg mb-2">{kit.type}</h4>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">{kit.description}</p>
                  
                  <div className="space-y-2 mb-4 text-xs">
                    <div>
                      <span className="font-medium">Format:</span> {kit.format}
                    </div>
                    <div>
                      <span className="font-medium">Updated:</span> {kit.updated}
                    </div>
                  </div>
                  
                  <Button size="sm" variant="outline" className="w-full">
                    <Download className="h-4 w-4 mr-2" />
                    Download
                  </Button>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card className="mb-12">
          <CardHeader>
            <CardTitle className="flex items-center text-2xl">
              <Mail className="h-7 w-7 mr-3" />
              Media Contact
            </CardTitle>
            <CardDescription>
              Get in touch for interviews, quotes, or additional information
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-8">
              <div>
                <h4 className="font-semibold text-lg mb-4">Press Inquiries</h4>
                <div className="space-y-3">
                  <div className="flex items-center">
                    <Mail className="h-4 w-4 mr-3 text-slate-500" />
                    <a href="mailto:press@codeflowops.com" className="text-blue-600 hover:underline">
                      press@codeflowops.com
                    </a>
                  </div>
                  <div className="flex items-center">
                    <Globe className="h-4 w-4 mr-3 text-slate-500" />
                    <span className="text-sm">Response within 24 hours</span>
                  </div>
                  <div className="flex items-center">
                    <Calendar className="h-4 w-4 mr-3 text-slate-500" />
                    <span className="text-sm">Interview scheduling available</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold text-lg mb-4">What We Can Provide</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <Check className="h-4 w-4 text-green-600 mr-2" />
                    <span>Executive interviews and quotes</span>
                  </div>
                  <div className="flex items-center">
                    <Check className="h-4 w-4 text-green-600 mr-2" />
                    <span>Product demonstrations and trials</span>
                  </div>
                  <div className="flex items-center">
                    <Check className="h-4 w-4 text-green-600 mr-2" />
                    <span>Industry data and market insights</span>
                  </div>
                  <div className="flex items-center">
                    <Check className="h-4 w-4 text-green-600 mr-2" />
                    <span>Customer success stories and case studies</span>
                  </div>
                  <div className="flex items-center">
                    <Check className="h-4 w-4 text-green-600 mr-2" />
                    <span>High-resolution images and video content</span>
                  </div>
                  <div className="flex items-center">
                    <Check className="h-4 w-4 text-green-600 mr-2" />
                    <span>Expert commentary on DevOps trends</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            CodeFlowOps Press Kit - All materials are available for editorial use. 
            Please credit CodeFlowOps in all coverage.
          </p>
          <p className="mt-2">
            For licensing inquiries or custom assets: <a href="mailto:press@codeflowops.com" className="text-blue-600 hover:underline">press@codeflowops.com</a>
          </p>
          <p className="mt-4 font-semibold">
            © 2025 CodeFlowOps. All rights reserved.
          </p>
        </div>
      </div>
    </div>
  )
}
