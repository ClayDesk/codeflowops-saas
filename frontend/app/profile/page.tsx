'use client'

import React, { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { useTheme } from 'next-themes'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { 
  User, 
  Calendar, 
  Mail, 
  Shield, 
  CreditCard, 
  History, 
  Settings,
  CheckCircle,
  XCircle,
  Clock,
  Globe,
  Github,
  Loader2,
  Edit,
  Save,
  X,
  Trash2,
  Camera,
  Upload,
  Sun,
  Moon
} from 'lucide-react'

interface Deployment {
  id: string
  name: string
  repository: string
  status: 'success' | 'failed' | 'pending' | 'building'
  url?: string
  createdAt?: string
  created_at?: string  // Support both naming conventions
  technology?: string
}

interface Subscription {
  plan: 'trial' | 'free' | 'starter' | 'pro' | 'enterprise'
  status: 'active' | 'cancelled' | 'expired'
  currentPeriodEnd: string
  deployments: {
    used: number
    limit: number
  }
}

export default function ProfilePage() {
  const searchParams = useSearchParams()
  const { 
    user, 
    isAuthenticated, 
    fetchUserProfile, 
    updateUserProfile, 
    fetchUserDeployments, 
    clearDeploymentHistory,
    profilePicture,
    updateProfilePicture,
    removeProfilePicture
  } = useAuth()
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [subscription, setSubscription] = useState<Subscription | null>(null)
  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || ''
  })
  const [isUploadingPicture, setIsUploadingPicture] = useState(false)
  const [activeTab, setActiveTab] = useState('overview')

  // Fetch user data from API
  useEffect(() => {
    const fetchUserData = async () => {
      if (!isAuthenticated) return
      
      try {
        setIsLoading(true)
        
        // Use auth context functions for consistent error handling
        const profileResponse = await fetchUserProfile()
        if (profileResponse.user) {
          setProfileData({
            full_name: profileResponse.user.full_name || '',
            email: profileResponse.user.email || ''
          })
        }
        if (profileResponse.subscription) {
          setSubscription(profileResponse.subscription)
        }
        
        // Fetch user deployments
        const deploymentsResponse = await fetchUserDeployments()
        if (deploymentsResponse.deployments) {
          setDeployments(deploymentsResponse.deployments)
        }
      } catch (error) {
        console.error('Error fetching user data:', error)
        // Set empty deployments if API fails - don't use hardcoded fallback
        setDeployments([])
        
        setSubscription({
          plan: 'trial',
          status: 'active',
          currentPeriodEnd: '2025-09-21T00:00:00Z',
          deployments: {
            used: 0,
            limit: 5
          }
        })
      } finally {
        setIsLoading(false)
      }
    }

    if (isAuthenticated) {
      fetchUserData()
    }
  }, [isAuthenticated, fetchUserProfile, fetchUserDeployments])

  // Handle tab selection from URL parameters
  useEffect(() => {
    const tab = searchParams.get('tab')
    if (tab && ['overview', 'deployments', 'subscription', 'settings'].includes(tab)) {
      setActiveTab(tab)
    }
  }, [searchParams])

  const handleUpdateProfile = async () => {
    try {
      setIsLoading(true)
      await updateUserProfile(profileData)
      setIsEditing(false)
    } catch (error) {
      console.error('Error updating profile:', error)
    } finally {
      setIsLoading(false)
    }
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircle className="h-4 w-4 text-green-500" />
      case 'failed':
        return <XCircle className="h-4 w-4 text-red-500" />
      case 'building':
      case 'pending':
        return <Clock className="h-4 w-4 text-yellow-500" />
      default:
        return <Clock className="h-4 w-4 text-gray-500" />
    }
  }

  const getStatusBadge = (status: string) => {
    const variants = {
      success: 'default',
      failed: 'destructive',
      building: 'secondary',
      pending: 'outline'
    } as const
    
    return (
      <Badge variant={variants[status as keyof typeof variants] || 'outline'}>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    )
  }

  const getPlanBadge = (plan: string) => {
    const colors = {
      trial: 'bg-blue-100 text-blue-800',
      free: 'bg-gray-100 text-gray-800',
      starter: 'bg-green-100 text-green-800',
      pro: 'bg-purple-100 text-purple-800',
      enterprise: 'bg-orange-100 text-orange-800'
    } as const

    return (
      <Badge className={colors[plan as keyof typeof colors] || colors.trial}>
        {plan.toUpperCase()}
      </Badge>
    )
  }

  // Filter deployments to show only last 7 days
  const getRecentDeployments = () => {
    const sevenDaysAgo = new Date()
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7)
    
    return deployments.filter(deployment => {
      const dateString = deployment.createdAt || deployment.created_at
      if (!dateString) return false
      const deploymentDate = new Date(dateString)
      return deploymentDate >= sevenDaysAgo
    })
  }

  // Handle clearing deployment history
  const handleClearHistory = async () => {
    try {
      setIsLoading(true)
      
      // Call the API to clear history through auth context
      await clearDeploymentHistory()
      
      // Refetch deployments from backend to get the actual cleared state
      try {
        const deploymentsResponse = await fetchUserDeployments()
        if (deploymentsResponse.deployments) {
          setDeployments(deploymentsResponse.deployments)
        } else {
          setDeployments([])
        }
      } catch (fetchError) {
        console.warn('Failed to refetch deployments after clear, setting to empty:', fetchError)
        setDeployments([])
      }
      
      console.log('Deployment history cleared successfully')
      
    } catch (error) {
      console.error('Error clearing deployment history:', error)
      console.warn('Failed to clear deployment history')
    } finally {
      setIsLoading(false)
    }
  }

  // Handle profile picture upload
  const handleProfilePictureUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    try {
      setIsUploadingPicture(true)
      await updateProfilePicture(file)
      console.log('Profile picture uploaded successfully')
    } catch (error) {
      console.error('Error uploading profile picture:', error)
      alert(error instanceof Error ? error.message : 'Failed to upload profile picture. Please try again.')
    } finally {
      setIsUploadingPicture(false)
    }
  }

  // Handle profile picture removal
  const handleRemoveProfilePicture = () => {
    removeProfilePicture()
    console.log('Profile picture removed successfully')
  }

  if (!isAuthenticated) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <Shield className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
              <h2 className="text-xl font-semibold mb-2">Authentication Required</h2>
              <p className="text-muted-foreground mb-4">Please sign in to view your profile.</p>
              <Button asChild>
                <a href="/login">Sign In</a>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    )
  }

  const userInitials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase()
    : user?.email?.charAt(0).toUpperCase() || 'U'

  return (
    <div className="min-h-screen bg-gray-50 dark:bg-gray-900 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center space-x-4">
            <div className="relative group">
              <Avatar className="h-16 w-16">
                {profilePicture ? (
                  <AvatarImage 
                    src={profilePicture} 
                    alt="Profile picture" 
                    className="avatar-image"
                  />
                ) : null}
                <AvatarFallback className="bg-primary text-primary-foreground text-lg">
                  {userInitials}
                </AvatarFallback>
              </Avatar>
              
              {/* Upload overlay */}
              <div className="absolute inset-0 bg-black bg-opacity-50 rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-center">
                <label htmlFor="profile-picture-upload" className="cursor-pointer">
                  <Camera className="h-6 w-6 text-white" />
                  <input
                    id="profile-picture-upload"
                    type="file"
                    accept="image/*"
                    onChange={handleProfilePictureUpload}
                    className="hidden"
                    disabled={isUploadingPicture}
                  />
                </label>
              </div>
              
              {/* Loading indicator */}
              {isUploadingPicture && (
                <div className="absolute inset-0 bg-black bg-opacity-50 rounded-full flex items-center justify-center">
                  <Loader2 className="h-6 w-6 text-white animate-spin" />
                </div>
              )}
            </div>
            
            <div className="flex-1">
              <div className="flex items-center space-x-3">
                <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">
                  {user?.full_name || 'User Profile'}
                </h1>
                {profilePicture && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={handleRemoveProfilePicture}
                    className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-950"
                  >
                    <X className="h-4 w-4 mr-1" />
                    Remove Photo
                  </Button>
                )}
              </div>
              <p className="text-gray-600 dark:text-gray-400">{user?.email}</p>
              <p className="text-sm text-gray-500 dark:text-gray-500 mt-1">
                Hover over avatar to change profile picture
              </p>
            </div>
          </div>
        </div>

        <Tabs value={activeTab} onValueChange={setActiveTab} className="space-y-6">
          <TabsList className="grid w-full grid-cols-4">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="deployments">Deployments</TabsTrigger>
            <TabsTrigger value="subscription">Subscription</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>

          <TabsContent value="overview" className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Stats Cards */}
              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Total Deployments</p>
                      <p className="text-2xl font-bold">{deployments.length}</p>
                    </div>
                    <Globe className="h-8 w-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Successful Deployments</p>
                      <p className="text-2xl font-bold">
                        {deployments.filter(d => d.status === 'success').length}
                      </p>
                    </div>
                    <CheckCircle className="h-8 w-8 text-green-500" />
                  </div>
                </CardContent>
              </Card>

              <Card>
                <CardContent className="pt-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm font-medium text-muted-foreground">Current Plan</p>
                      <p className="text-xl font-bold flex items-center gap-2">
                        {subscription?.plan.toUpperCase()}
                        {getPlanBadge(subscription?.plan || 'trial')}
                      </p>
                    </div>
                    <CreditCard className="h-8 w-8 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Recent Deployments */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <History className="h-5 w-5" />
                  Recent Deployments
                </CardTitle>
                <CardDescription>
                  Your latest deployment activity
                </CardDescription>
              </CardHeader>
              <CardContent>
                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : deployments.length === 0 ? (
                  <div className="text-center py-8">
                    <Globe className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <p className="text-muted-foreground">No deployments yet</p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {deployments.slice(0, 3).map((deployment) => (
                      <div key={deployment.id} className="flex items-center justify-between p-4 border rounded-lg">
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(deployment.status)}
                          <div>
                            <p className="font-medium">{deployment.name}</p>
                            <p className="text-sm text-muted-foreground">{deployment.repository}</p>
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <Badge variant="outline">{deployment.technology}</Badge>
                          {getStatusBadge(deployment.status)}
                          <p className="text-sm text-muted-foreground">
                            {new Date(deployment.createdAt || deployment.created_at || '').toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="deployments" className="space-y-6">
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-4">
                <div>
                  <CardTitle className="flex items-center gap-2">
                    <Globe className="h-5 w-5" />
                    Recent Deployments
                  </CardTitle>
                  <CardDescription>
                    Deployment history from the last 7 days
                  </CardDescription>
                </div>
                <Button 
                  variant="outline" 
                  size="sm" 
                  onClick={handleClearHistory}
                  disabled={isLoading || getRecentDeployments().length === 0}
                  className="text-red-600 hover:text-red-700 hover:bg-red-50 dark:text-red-400 dark:hover:text-red-300 dark:hover:bg-red-950"
                >
                  <Trash2 className="h-4 w-4 mr-2" />
                  Clear History
                </Button>
              </CardHeader>
              <CardContent>
                {/* Auto-deletion notice */}
                <Alert className="mb-4 bg-blue-50 border-blue-200">
                  <History className="h-4 w-4" />
                  <AlertDescription className="text-blue-700">
                    <strong>Note:</strong> Deployment history is automatically deleted after 7 days for security and storage optimization.
                  </AlertDescription>
                </Alert>

                {isLoading ? (
                  <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-8 w-8 animate-spin" />
                  </div>
                ) : getRecentDeployments().length === 0 ? (
                  <div className="text-center py-8">
                    <History className="h-12 w-12 mx-auto mb-4 text-muted-foreground" />
                    <h3 className="text-lg font-medium mb-2">No Recent Deployments</h3>
                    <p className="text-muted-foreground">
                      You haven't deployed anything in the last 7 days.
                    </p>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {getRecentDeployments().map((deployment) => (
                      <div key={deployment.id} className="flex items-center justify-between p-4 border rounded-lg hover:bg-gray-50">
                        <div className="flex items-center space-x-3">
                          {getStatusIcon(deployment.status)}
                          <div>
                            <p className="font-medium">{deployment.name}</p>
                            <div className="flex items-center space-x-2 text-sm text-muted-foreground">
                              <Github className="h-3 w-3" />
                              <span>{deployment.repository}</span>
                            </div>
                            {deployment.url && (
                              <div className="flex items-center space-x-2 text-sm text-blue-600">
                                <Globe className="h-3 w-3" />
                                <a href={deployment.url} target="_blank" rel="noopener noreferrer" className="hover:underline">
                                  {deployment.url}
                                </a>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center space-x-3">
                          <Badge variant="outline">{deployment.technology}</Badge>
                          {getStatusBadge(deployment.status)}
                          <div className="text-right">
                            <p className="text-sm text-muted-foreground">
                              {new Date(deployment.createdAt || deployment.created_at || '').toLocaleDateString()}
                            </p>
                            <p className="text-xs text-muted-foreground">
                              {new Date(deployment.createdAt || deployment.created_at || '').toLocaleTimeString()}
                            </p>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="subscription" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Current Plan */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <CreditCard className="h-5 w-5" />
                    Current Plan
                  </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {subscription && (
                    <>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Plan:</span>
                        {getPlanBadge(subscription.plan)}
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Status:</span>
                        <Badge variant={subscription.status === 'active' ? 'default' : 'secondary'}>
                          {subscription.status.toUpperCase()}
                        </Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="font-medium">Deployments:</span>
                        <span>{subscription.deployments.used} / {subscription.deployments.limit}</span>
                      </div>
                      <div className="w-full bg-gray-200 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full" 
                          style={{ width: `${(subscription.deployments.used / subscription.deployments.limit) * 100}%` }}
                        ></div>
                      </div>
                      {subscription.plan === 'trial' && (
                        <Alert>
                          <Calendar className="h-4 w-4" />
                          <AlertDescription>
                            Your trial expires on {new Date(subscription.currentPeriodEnd).toLocaleDateString()}
                          </AlertDescription>
                        </Alert>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Plan Actions */}
              <Card>
                <CardHeader>
                  <CardTitle>Plan Management</CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                  {subscription?.plan === 'trial' ? (
                    <div className="space-y-3">
                      <p className="text-sm text-muted-foreground">
                        Upgrade your plan to unlock more features and deployments.
                      </p>
                      <Button className="w-full text-white dark:text-white">
                        Upgrade to Pro
                      </Button>
                      <Button variant="outline" className="w-full dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                        View All Plans
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-sm text-muted-foreground">
                        Manage your subscription and billing.
                      </p>
                      <Button variant="outline" className="w-full dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                        Update Payment Method
                      </Button>
                      <Button variant="outline" className="w-full dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                        View Billing History
                      </Button>
                      <Button variant="destructive" className="w-full text-white dark:text-white">
                        Cancel Subscription
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>

            {/* Pricing Plans */}
            <Card>
              <CardHeader>
                <CardTitle>Available Plans</CardTitle>
                <CardDescription>
                  Choose the plan that best fits your needs
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  {/* Free Plan */}
                  <div className="border rounded-lg p-6 space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold">Free</h3>
                      <p className="text-2xl font-bold">$0<span className="text-sm font-normal">/forever</span></p>
                      <p className="text-sm text-muted-foreground mt-2">Perfect for personal projects and learning</p>
                    </div>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        5 React/Static deployments per month
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Public repositories only
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Basic AWS infrastructure
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Standard build times
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Community support
                      </li>
                      <li className="flex items-center gap-2 opacity-40">
                        <XCircle className="h-4 w-4 text-gray-400" />
                        Private repositories
                      </li>
                      <li className="flex items-center gap-2 opacity-40">
                        <XCircle className="h-4 w-4 text-gray-400" />
                        Custom domains
                      </li>
                      <li className="flex items-center gap-2 opacity-40">
                        <XCircle className="h-4 w-4 text-gray-400" />
                        Priority support
                      </li>
                      <li className="flex items-center gap-2 opacity-40">
                        <XCircle className="h-4 w-4 text-gray-400" />
                        Advanced analytics
                      </li>
                    </ul>
                    <Button 
                      variant={subscription?.plan === 'free' ? 'secondary' : 'default'}
                      className="w-full text-white dark:text-white"
                      disabled={subscription?.plan === 'free'}
                    >
                      {subscription?.plan === 'free' ? 'Current Plan' : 'Get Started Free'}
                    </Button>
                  </div>

                  {/* Pro Plan */}
                  <div className="border-2 border-blue-500 rounded-lg p-6 space-y-4 relative">
                    <div className="absolute -top-3 left-1/2 transform -translate-x-1/2">
                      <Badge className="bg-blue-500">Most Popular</Badge>
                    </div>
                    <div>
                      <h3 className="text-lg font-semibold">Pro</h3>
                      <p className="text-2xl font-bold">$12<span className="text-sm font-normal">/per month</span></p>
                      <p className="text-sm text-muted-foreground mt-2">Best for professional developers and small teams</p>
                    </div>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Unlimited React & Static deployments
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Private repositories
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Custom domains with SSL
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Fast build times
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Email support
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Advanced analytics
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Environment variables
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Deployment previews
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        GitHub integration
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        CloudFront CDN
                      </li>
                      <li className="flex items-center gap-2 opacity-40">
                        <XCircle className="h-4 w-4 text-gray-400" />
                        White-label options
                      </li>
                      <li className="flex items-center gap-2 opacity-40">
                        <XCircle className="h-4 w-4 text-gray-400" />
                        Dedicated support
                      </li>
                      <li className="flex items-center gap-2 opacity-40">
                        <XCircle className="h-4 w-4 text-gray-400" />
                        Custom integrations
                      </li>
                    </ul>
                    <Button 
                      variant={subscription?.plan === 'pro' ? 'secondary' : 'default'}
                      className="w-full text-white dark:text-white"
                      disabled={subscription?.plan === 'pro'}
                    >
                      {subscription?.plan === 'pro' ? 'Current Plan' : 'Start Pro Trial'}
                    </Button>
                  </div>

                  {/* Enterprise Plan */}
                  <div className="border rounded-lg p-6 space-y-4">
                    <div>
                      <h3 className="text-lg font-semibold">Enterprise</h3>
                      <p className="text-2xl font-bold">Custom</p>
                      <p className="text-sm text-muted-foreground mt-2">For large teams and organizations</p>
                    </div>
                    <ul className="space-y-2 text-sm">
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Everything in Pro
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        White-label solution
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Dedicated support manager
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Custom integrations & APIs
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        SLA guarantees (99.9% uptime)
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Advanced security & compliance
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Team management & permissions
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Priority builds & deployment
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Custom workflows & automation
                      </li>
                      <li className="flex items-center gap-2">
                        <CheckCircle className="h-4 w-4 text-green-500" />
                        Multi-region deployments
                      </li>
                    </ul>
                    <Button 
                      variant={subscription?.plan === 'enterprise' ? 'secondary' : 'default'}
                      className="w-full text-white dark:text-white"
                      disabled={subscription?.plan === 'enterprise'}
                    >
                      {subscription?.plan === 'enterprise' ? 'Current Plan' : 'Contact Sales'}
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="settings" className="space-y-6">
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              {/* Profile Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <User className="h-5 w-5" />
                    Profile Information
                  </CardTitle>
                  <CardDescription>
                    Update your personal information
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  {/* Profile Picture Section */}
                  <div className="space-y-2">
                    <Label>Profile Picture</Label>
                    <div className="flex items-center gap-4">
                      <Avatar className="h-12 w-12">
                        {profilePicture ? (
                          <AvatarImage 
                            src={profilePicture} 
                            alt="Profile picture" 
                            className="avatar-image"
                          />
                        ) : null}
                        <AvatarFallback className="bg-primary text-primary-foreground">
                          {userInitials}
                        </AvatarFallback>
                      </Avatar>
                      <div className="flex gap-2">
                        <label htmlFor="settings-profile-picture-upload">
                          <Button variant="outline" size="sm" asChild disabled={isUploadingPicture} className="dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                            <div className="cursor-pointer">
                              {isUploadingPicture ? (
                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              ) : (
                                <Upload className="h-4 w-4 mr-2" />
                              )}
                              Upload
                            </div>
                          </Button>
                          <input
                            id="settings-profile-picture-upload"
                            type="file"
                            accept="image/*"
                            onChange={handleProfilePictureUpload}
                            className="hidden"
                            disabled={isUploadingPicture}
                          />
                        </label>
                        {profilePicture && (
                          <Button
                            variant="outline"
                            size="sm"
                            onClick={handleRemoveProfilePicture}
                            className="text-red-600 hover:text-red-700 dark:text-red-400 dark:hover:text-red-300"
                          >
                            <Trash2 className="h-4 w-4 mr-2" />
                            Remove
                          </Button>
                        )}
                      </div>
                    </div>
                    <p className="text-sm text-gray-500">
                      JPG, PNG or GIF (max. 5MB)
                    </p>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="fullName">Full Name</Label>
                    <div className="flex gap-2">
                      <Input
                        id="fullName"
                        value={profileData.full_name}
                        onChange={(e) => setProfileData(prev => ({ ...prev, full_name: e.target.value }))}
                        disabled={!isEditing}
                      />
                      {!isEditing && (
                        <Button variant="outline" size="icon" onClick={() => setIsEditing(true)} className="dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                          <Edit className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                  
                  <div className="space-y-2">
                    <Label htmlFor="email">Email Address</Label>
                    <Input
                      id="email"
                      type="email"
                      value={profileData.email}
                      disabled
                      className="bg-gray-50 dark:bg-gray-800 dark:text-white dark:border-gray-600"
                    />
                    <p className="text-xs text-muted-foreground">
                      Email address cannot be changed. Contact support if needed.
                    </p>
                  </div>

                  {isEditing && (
                    <div className="flex gap-2">
                      <Button onClick={handleUpdateProfile} disabled={isLoading} className="text-white dark:text-white">
                        {isLoading ? (
                          <>
                            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                            Saving...
                          </>
                        ) : (
                          <>
                            <Save className="mr-2 h-4 w-4" />
                            Save Changes
                          </>
                        )}
                      </Button>
                      <Button variant="outline" onClick={() => setIsEditing(false)} className="dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                        <X className="mr-2 h-4 w-4" />
                        Cancel
                      </Button>
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Security Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Shield className="h-5 w-5" />
                    Security
                  </CardTitle>
                  <CardDescription>
                    Manage your account security
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <Button variant="outline" className="w-full justify-start dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                      Change Password
                    </Button>
                    <Button variant="outline" className="w-full justify-start dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                      Two-Factor Authentication
                    </Button>
                    <Button variant="outline" className="w-full justify-start dark:text-white dark:border-gray-600 dark:hover:bg-gray-700">
                      Connected Accounts
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* Notification Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Mail className="h-5 w-5" />
                    Notifications
                  </CardTitle>
                  <CardDescription>
                    Configure your notification preferences
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Deployment Updates</p>
                        <p className="text-sm text-muted-foreground">Get notified when deployments complete</p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Weekly Reports</p>
                        <p className="text-sm text-muted-foreground">Receive weekly deployment summaries</p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">Security Alerts</p>
                        <p className="text-sm text-muted-foreground">Important security notifications</p>
                      </div>
                      <input type="checkbox" defaultChecked className="rounded" />
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Theme Settings */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Settings className="h-5 w-5" />
                    Theme
                  </CardTitle>
                  <CardDescription>
                    Choose your preferred color scheme
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <ThemeSelector />
                </CardContent>
              </Card>

              {/* Danger Zone */}
              <Card className="border-red-200">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-red-600">
                    <XCircle className="h-5 w-5" />
                    Danger Zone
                  </CardTitle>
                  <CardDescription>
                    Irreversible actions that affect your account
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <Button variant="outline" className="w-full justify-start border-red-200 text-red-600 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950 dark:hover:text-red-300">
                      Download Account Data
                    </Button>
                    <Button variant="destructive" className="w-full justify-start text-white dark:text-white">
                      Delete Account
                    </Button>
                  </div>
                  <Alert className="border-red-200">
                    <XCircle className="h-4 w-4" />
                    <AlertDescription className="text-red-600">
                      Account deletion is permanent and cannot be undone.
                    </AlertDescription>
                  </Alert>
                </CardContent>
              </Card>
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}

// Theme Selector Component
function ThemeSelector() {
  const { theme, setTheme, resolvedTheme } = useTheme()

  const themes = [
    { name: 'Light', value: 'light', icon: Sun },
    { name: 'Dark', value: 'dark', icon: Moon },
    { name: 'System', value: 'system', icon: Settings },
  ]

  return (
    <div className="space-y-3">
      {themes.map((themeOption) => {
        const Icon = themeOption.icon
        const isActive = theme === themeOption.value
        
        return (
          <Button
            key={themeOption.value}
            variant={isActive ? "default" : "outline"}
            className={`w-full justify-start ${
              isActive 
                ? "text-white dark:text-white" 
                : "dark:text-white dark:border-gray-600 dark:hover:bg-gray-700"
            }`}
            onClick={() => setTheme(themeOption.value)}
          >
            <Icon className="h-4 w-4 mr-2" />
            {themeOption.name}
            {themeOption.value === 'system' && resolvedTheme && (
              <span className="ml-auto text-xs text-muted-foreground">
                ({resolvedTheme})
              </span>
            )}
          </Button>
        )
      })}
    </div>
  )
}
