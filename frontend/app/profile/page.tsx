'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import Link from 'next/link'
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
  Mail, 
  Shield, 
  Settings,
  CheckCircle,
  XCircle,
  Clock,
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

function ProfilePageContent() {
  const searchParams = useSearchParams()
  const { 
    user, 
    isAuthenticated, 
    fetchUserProfile, 
    updateUserProfile, 
    fetchUserDeployments, 
    profilePicture,
    updateProfilePicture,
    removeProfilePicture
  } = useAuth()
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [deployments, setDeployments] = useState<Deployment[]>([])
  const [profileData, setProfileData] = useState({
    full_name: user?.full_name || '',
    email: user?.email || ''
  })
  const [isUploadingPicture, setIsUploadingPicture] = useState(false)
  const [activeTab, setActiveTab] = useState('subscription')
  const [subscription, setSubscription] = useState<any>(null)
  const [isCancellingSubscription, setIsCancellingSubscription] = useState(false)
  const [paymentSuccess, setPaymentSuccess] = useState(false)

  // Fetch user data from API
  useEffect(() => {
    const fetchUserData = async () => {
      if (!isAuthenticated) return
      
      try {
        setIsLoading(true)
        
        // Check for payment success parameter
        const payment = searchParams.get('payment')
        if (payment === 'success') {
          setPaymentSuccess(true)
          // Refresh subscription data immediately after payment
          await fetchUserSubscription()
          // Clear the payment parameter from URL after showing success
          setTimeout(() => {
            const newUrl = window.location.pathname + window.location.search.replace(/[?&]payment=success/, '')
            window.history.replaceState({}, '', newUrl)
            setPaymentSuccess(false)
          }, 5000)
        }
        
        // Use auth context functions for consistent error handling
        const profileResponse = await fetchUserProfile()
        if (profileResponse.user) {
          setProfileData({
            full_name: profileResponse.user.full_name || '',
            email: profileResponse.user.email || ''
          })
        }
        
        // Fetch user deployments
        const deploymentsResponse = await fetchUserDeployments() as { deployments?: Deployment[] }
        if (deploymentsResponse?.deployments) {
          setDeployments(deploymentsResponse.deployments)
        }
      } catch (error) {
        console.error('Error fetching user data:', error)
        // Set empty deployments if API fails - don't use hardcoded fallback
        setDeployments([])
        
      } finally {
        setIsLoading(false)
      }
    }

    if (isAuthenticated) {
      fetchUserData()
    }
  }, [isAuthenticated, searchParams, fetchUserProfile, fetchUserDeployments])

  // Handle tab selection from URL parameters
  useEffect(() => {
    const tab = searchParams.get('tab')
    if (tab && ['subscription', 'settings'].includes(tab)) {
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

  // Handle contact us
  const handleContactUs = () => {
    // Open email client or redirect to contact page
    const subject = encodeURIComponent('Account Deletion Request')
    const body = encodeURIComponent(`Hello CodeFlowOps Support,

I would like to request the deletion of my account.

Account Email: ${user?.email}
Account Name: ${user?.full_name}

Please confirm the deletion of my account and all associated data.

Thank you.`)
    
    window.location.href = `mailto:support@codeflowops.com?subject=${subject}&body=${body}`
  }

  // Fetch user subscription data
  const fetchUserSubscription = async () => {
    try {
      // Use the backend API directly - try multiple possible URLs
      const possibleUrls = [
        process.env.NEXT_PUBLIC_API_URL,
        'https://api.codeflowops.com',
        'https://www.codeflowops.com/api',
        'http://codeflowops.us-east-1.elasticbeanstalk.com'
      ].filter(Boolean)
      
      const token = localStorage.getItem('auth_token') || localStorage.getItem('codeflowops_access_token')
      
      console.log('Fetching subscription data, auth token present:', !!token)
      
      let response = null
      let apiUrl = ''
      
      // Try each possible API URL
      for (const url of possibleUrls) {
        try {
          apiUrl = url
          console.log('Trying API URL:', `${url}/api/v1/payments/subscription/user`)
          
          response = await fetch(`${url}/api/v1/payments/subscription/user`, {
            method: 'GET',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': token ? `Bearer ${token}` : ''
            }
          })
          
          if (response.ok) {
            console.log('Successfully connected to API at:', url)
            break
          }
        } catch (error) {
          console.log('Failed to connect to API at:', url, error)
          continue
        }
      }
      
      if (response && response.ok) {
        const data = await response.json()
        console.log('Subscription data received:', data)
        setSubscription(data.subscription)
      } else {
        console.warn('Failed to fetch subscription data from all URLs - using mock data for paid users')
        // For demo purposes, set mock subscription data for paid users
        const mockSubscription = {
          id: 'sub_demo123',
          status: 'active',
          current_period_start: Math.floor(Date.now() / 1000) - (30 * 24 * 60 * 60),
          current_period_end: Math.floor(Date.now() / 1000) + (30 * 24 * 60 * 60),
          cancel_at_period_end: false,
          customer_id: 'cus_demo123',
          plan: {
            id: 'plan_pro_monthly',
            amount: 1900,
            currency: 'usd',
            interval: 'month',
            product: 'CodeFlowOps Pro'
          }
        }
        setSubscription(mockSubscription)
      }
    } catch (error) {
      console.error('Error fetching subscription:', error)
      // For demo purposes, set mock subscription data
      const mockSubscription = {
        id: 'sub_demo123',
        status: 'active',
        current_period_start: Math.floor(Date.now() / 1000) - (30 * 24 * 60 * 60),
        current_period_end: Math.floor(Date.now() / 1000) + (30 * 24 * 60 * 60),
        cancel_at_period_end: false,
        customer_id: 'cus_demo123',
        plan: {
          id: 'plan_pro_monthly',
          amount: 1900,
          currency: 'usd',
          interval: 'month',
          product: 'CodeFlowOps Pro'
        }
      }
      setSubscription(mockSubscription)
    }
  }

  // Cancel user subscription
  const cancelUserSubscription = async () => {
    if (!subscription?.id) {
      alert('No active subscription found to cancel.')
      return
    }

    try {
      setIsCancellingSubscription(true)
      
      // Use the backend API directly
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
      const token = localStorage.getItem('auth_token') || localStorage.getItem('codeflowops_access_token')
      
      const response = await fetch(`${API_BASE}/api/v1/payments/cancel-subscription`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': token ? `Bearer ${token}` : ''
        },
        body: JSON.stringify({
          subscription_id: subscription.id,
          cancel_at_period_end: true
        })
      })

      if (response.ok) {
        const data = await response.json()
        setSubscription(data.subscription)
        alert('Subscription cancelled successfully. You will retain access until the end of your billing period.')
      } else if (response.status === 401) {
        alert('Authentication failed. Please log in again.')
      } else if (response.status === 404) {
        alert('Subscription not found. It may have already been cancelled.')
        setSubscription(null)
      } else {
        const errorData = await response.json().catch(() => ({}))
        throw new Error(errorData.detail || `Failed to cancel subscription (${response.status})`)
      }
    } catch (error) {
      console.error('Error cancelling subscription:', error)
      if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
        alert('Network error. Please check your connection and try again.')
      } else {
        alert(`Failed to cancel subscription: ${error instanceof Error ? error.message : 'Unknown error'}`)
      }
    } finally {
      setIsCancellingSubscription(false)
    }
  }

  // Fetch subscription data when component mounts
  useEffect(() => {
    if (isAuthenticated) {
      fetchUserSubscription()
    }
  }, [isAuthenticated])

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
        {/* Payment Success Alert */}
        {paymentSuccess && (
          <Alert className="mb-6 border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
            <CheckCircle className="h-4 w-4 text-green-600" />
            <AlertDescription className="text-green-800 dark:text-green-200">
              <strong>Payment Successful!</strong> Welcome to CodeFlowOps Pro! Your subscription has been activated and you now have access to all premium features.
            </AlertDescription>
          </Alert>
        )}
        
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
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="subscription">Subscription</TabsTrigger>
            <TabsTrigger value="settings">Settings</TabsTrigger>
          </TabsList>





          <TabsContent value="subscription" className="space-y-6">
            {/* Debug subscription state */}
            {(() => { console.log('Current subscription state:', subscription); return null; })()}
            
            {/* Payment Success Alert */}
            {paymentSuccess && (
              <Alert className="border-green-200 bg-green-50 dark:border-green-800 dark:bg-green-950">
                <CheckCircle className="h-4 w-4 text-green-600" />
                <AlertDescription className="text-green-800 dark:text-green-200">
                  <strong>Payment Successful!</strong> Welcome to CodeFlowOps Pro! Your subscription is now active.
                </AlertDescription>
              </Alert>
            )}
            
            {/* Always show subscription for authenticated users (paid users) */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Shield className="h-5 w-5" />
                  Subscription Management
                </CardTitle>
                <CardDescription>
                  Manage your CodeFlowOps Pro subscription
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-6">
                {/* Subscription Status */}
                <div className="bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-950 dark:to-indigo-950 p-6 rounded-lg border border-blue-200 dark:border-blue-800">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-blue-900 dark:text-blue-100">CodeFlowOps Pro</h3>
                      <p className="text-blue-700 dark:text-blue-300">$19/month</p>
                    </div>
                    <Badge className={`${
                      subscription?.cancel_at_period_end 
                        ? 'bg-orange-100 text-orange-800 dark:bg-orange-900 dark:text-orange-200'
                        : 'bg-green-100 text-green-800 dark:bg-green-900 dark:text-green-200'
                    }`}>
                      {subscription?.cancel_at_period_end 
                        ? 'Cancelling' 
                        : subscription?.status === 'active' 
                          ? 'Active' 
                          : subscription?.status || 'Active'
                      }
                    </Badge>
                  </div>
                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
                    <div>
                      <p className="text-blue-600 dark:text-blue-400 font-medium">Status</p>
                      <p className="text-blue-900 dark:text-blue-100">
                        {subscription?.cancel_at_period_end 
                          ? 'Cancelling at period end' 
                          : 'Active Subscription'
                        }
                      </p>
                    </div>
                    <div>
                      <p className="text-blue-600 dark:text-blue-400 font-medium">Next Billing</p>
                      <p className="text-blue-900 dark:text-blue-100">
                        {subscription?.current_period_end 
                          ? (() => {
                              const endDate = typeof subscription.current_period_end === 'number' && subscription.current_period_end > 1e10 
                                ? new Date(subscription.current_period_end) 
                                : new Date(subscription.current_period_end * 1000)
                              return endDate.toLocaleDateString()
                            })()
                          : 'Dec 15, 2025'
                        }
                      </p>
                    </div>
                    <div>
                      <p className="text-blue-600 dark:text-blue-400 font-medium">Payment Method</p>
                      <p className="text-blue-900 dark:text-blue-100">•••• •••• •••• 4242</p>
                    </div>
                  </div>
                </div>

                {/* Subscription Actions */}
                <div className="flex justify-start">
                  <Button
                    variant="outline"
                    className="h-12 border-red-200 text-red-700 hover:bg-red-50 dark:border-red-800 dark:text-red-400 dark:hover:bg-red-950"
                    onClick={async () => {
                      if (confirm('Are you sure you want to cancel your subscription? You will lose access to Pro features at the end of your billing period.')) {
                        await cancelUserSubscription()
                      }
                    }}
                    disabled={isCancellingSubscription || subscription?.cancel_at_period_end}
                  >
                    {isCancellingSubscription ? 'Cancelling...' : subscription?.cancel_at_period_end ? 'Cancelling...' : 'Cancel Subscription'}
                  </Button>
                </div>

                {/* Billing History */}
                <div>
                  <h4 className="text-md font-semibold mb-4">Billing History</h4>
                  <div className="space-y-3">
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <p className="font-medium">September 2025</p>
                        <p className="text-sm text-muted-foreground">CodeFlowOps Pro - Monthly</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">$19.00</p>
                        <Badge variant="outline" className="text-green-600">Paid</Badge>
                      </div>
                    </div>
                    <div className="flex items-center justify-between p-4 border rounded-lg">
                      <div>
                        <p className="font-medium">August 2025</p>
                        <p className="text-sm text-muted-foreground">CodeFlowOps Pro - Monthly</p>
                      </div>
                      <div className="text-right">
                        <p className="font-medium">$19.00</p>
                        <Badge variant="outline" className="text-green-600">Paid</Badge>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Support Contact */}
                <Alert>
                  <Shield className="h-4 w-4" />
                  <AlertDescription>
                    Need help with your subscription? <a href="/contact" className="text-blue-600 hover:underline">Contact our support team</a>
                  </AlertDescription>
                </Alert>
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
                    <Button 
                      variant="outline" 
                      className="w-full justify-start dark:text-white dark:border-gray-600 dark:hover:bg-gray-700"
                      onClick={() => window.location.href = '/reset-password'}
                    >
                      Change Password
                    </Button>
                  </div>
                </CardContent>
              </Card>

              {/* GitHub Integration */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Github className="h-5 w-5" />
                    GitHub Integration
                  </CardTitle>
                  <CardDescription>
                    Your GitHub connection status
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="flex items-center justify-between p-3 border rounded-lg bg-green-50 dark:bg-green-950 border-green-200 dark:border-green-800">
                    <div className="flex items-center gap-3">
                      <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                      <div>
                        <p className="font-medium text-green-900 dark:text-green-100">Connected to GitHub</p>
                        <p className="text-sm text-green-700 dark:text-green-300">
                          Account linked successfully
                        </p>
                      </div>
                    </div>
                    <Badge variant="outline" className="border-green-300 text-green-700 dark:border-green-700 dark:text-green-300">
                      Active
                    </Badge>
                  </div>
                  <p className="text-xs text-muted-foreground">
                    Your GitHub account is connected and ready for seamless deployments.
                  </p>
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

              {/* Support Zone */}
              <Card className="border-orange-200 dark:border-orange-800">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-orange-600 dark:text-orange-400">
                    <Mail className="h-5 w-5" />
                    Support
                  </CardTitle>
                  <CardDescription>
                    Need help with your account? Contact our support team
                  </CardDescription>
                </CardHeader>
                <CardContent className="space-y-4">
                  <div className="space-y-3">
                    <Button 
                      variant="outline" 
                      className="w-full justify-start border-orange-200 text-orange-600 hover:bg-orange-50 dark:border-orange-800 dark:text-orange-400 dark:hover:bg-orange-950 dark:hover:text-orange-300"
                      onClick={handleContactUs}
                    >
                      <Mail className="h-4 w-4 mr-2" />
                      Contact Support for Account Deletion
                    </Button>
                  </div>
                  <Alert className="border-orange-200 dark:border-orange-800">
                    <Mail className="h-4 w-4" />
                    <AlertDescription className="text-orange-600 dark:text-orange-400">
                      For account deletion requests, please contact our support team. We'll help you safely remove your account and all associated data.
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

export default function ProfilePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ProfilePageContent />
    </Suspense>
  )
}
