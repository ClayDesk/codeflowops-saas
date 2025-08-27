'use client'

import React, { useState, useEffect, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { useTheme } from 'next-themes'
import { useStripePayment } from '@/hooks/use-stripe-payment'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from "@/components/ui/badge"
import { SubscriptionPricing } from '@/components/profile/SubscriptionPricing'
import { BillingHistoryModal } from '@/components/profile/BillingHistoryModal'
import { QuotaDisplay } from '@/components/quota/QuotaDisplay'
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
  Moon,
  RefreshCw
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
  id?: string
  plan: 'trial' | 'free' | 'starter' | 'pro' | 'enterprise'
  status: 'active' | 'cancelled' | 'expired'
  currentPeriodEnd: string | null
  deployments: {
    used: number
    limit: number
  }
}

function ProfilePageContent() {
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
  const { 
    createSubscription, 
    upgradeSubscription, 
    cancelSubscription,
    loading: stripeLoading 
  } = useStripePayment({
    onSuccess: (result) => {
      if (result.client_secret) {
        // Redirect to Stripe checkout
        window.location.href = `/checkout?client_secret=${result.client_secret}`
      } else {
        // Refresh page to show updated subscription
        window.location.reload()
      }
    },
    onError: (error) => {
      alert(`Payment operation failed: ${error}`)
    }
  })
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

  // Stripe payment management functions
  const refreshSubscriptionStatus = async () => {
    try {
      const token = localStorage.getItem('codeflowops_access_token')
      const apiUrl = 'https://api.codeflowops.com'
      const response = await fetch(`${apiUrl}/api/v1/payments/user-subscription-status`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.subscription) {
          setSubscription({
            id: data.subscription.subscription_id,
            plan: data.subscription.plan_tier || 'free',
            status: data.subscription.status || 'active',
            currentPeriodEnd: data.subscription.current_period_end,
            deployments: {
              used: data.subscription.usage?.projects_count || 0,
              limit: data.subscription.plan?.max_projects || 5
            }
          })
        }
      }
    } catch (error) {
      console.error('Failed to refresh subscription status:', error)
    }
  }

  const handleUpgradeToPro = async () => {
    try {
      await createSubscription({
        planTier: 'pro',
        trialDays: 14,
        pricingContext: {
          source: 'profile_upgrade',
          current_plan: subscription?.plan
        }
      })
    } catch (error) {
      console.error('Upgrade failed:', error)
    }
  }

  const handleManagePaymentMethod = async () => {
    try {
      const token = localStorage.getItem('codeflowops_access_token')
      const apiUrl = 'https://api.codeflowops.com'
      const response = await fetch(`${apiUrl}/api/v1/payments/customer-portal`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      })
      
      if (response.ok) {
        const { url } = await response.json()
        window.location.href = url
      } else {
        alert('Unable to access payment management. Please try again.')
      }
    } catch (error) {
      console.error('Payment method management failed:', error)
      alert('Unable to access payment management. Please try again.')
    }
  }

  const handleViewBillingHistory = async () => {
    const token = localStorage.getItem('codeflowops_access_token')
    const apiUrl = 'https://api.codeflowops.com'
    const response = await fetch(`${apiUrl}/api/v1/payments/billing-history`, {
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      throw new Error('Failed to fetch billing history')
    }
    
    const billingData = await response.json()
    return billingData.invoices || []
  }

  const handleCancelSubscription = async () => {
    if (!subscription?.plan || subscription.plan === 'free') {
      alert('No active subscription to cancel.')
      return
    }

    const confirmed = confirm('Are you sure you want to cancel your subscription? You will lose access to premium features at the end of your billing period.')
    if (!confirmed) return

    try {
      // Call the cancel API directly since the hook expects different parameters
      const token = localStorage.getItem('codeflowops_access_token')
      const apiUrl = 'https://api.codeflowops.com'
      const response = await fetch(`${apiUrl}/api/v1/payments/cancel-subscription`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          subscription_id: subscription.id || 'current',
          at_period_end: true
        })
      })

      if (response.ok) {
        alert('Subscription cancelled successfully. You will retain access until the end of your billing period.')
        // Refresh the page to show updated subscription status
        window.location.reload()
      } else {
        const errorData = await response.json()
        alert(`Failed to cancel subscription: ${errorData.detail || 'Unknown error'}`)
      }
    } catch (error) {
      console.error('Subscription cancellation failed:', error)
      alert('Failed to cancel subscription. Please contact support.')
    }
  }

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
        
        // Process subscription data from billing API
        if (profileResponse.subscription) {
          const billingData = profileResponse.subscription
          
          // Transform billing data to match frontend subscription interface
          const transformedSubscription = {
            plan: billingData.plan?.tier || 'free',
            status: billingData.status || 'active',
            currentPeriodEnd: billingData.current_period_end || billingData.trial_end,
            deployments: {
              used: billingData.usage?.projects_count || 0,
              limit: billingData.plan?.max_projects || 5
            }
          }
          
          setSubscription(transformedSubscription)
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
        
        // Only set fallback subscription if no data was fetched at all
        if (!subscription) {
          setSubscription({
            plan: 'free',
            status: 'active',
            currentPeriodEnd: null,
            deployments: {
              used: 0,
              limit: 5
            }
          })
        }
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
    return (
      <Badge>
        {status.charAt(0).toUpperCase() + status.slice(1)}
      </Badge>
    )
  }

  const getPlanBadge = (plan: string) => {
    return (
      <Badge>
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
                          <Badge>{deployment.technology}</Badge>
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
                          <Badge>{deployment.technology}</Badge>
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
                        <Badge>
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
                            Your trial expires on {subscription.currentPeriodEnd ? new Date(subscription.currentPeriodEnd).toLocaleDateString() : 'N/A'}
                          </AlertDescription>
                        </Alert>
                      )}
                    </>
                  )}
                </CardContent>
              </Card>

              {/* Quota & Usage Display */}
              <QuotaDisplay 
                onUpgrade={() => setActiveTab('subscription')}
              />

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
                      <Button 
                        className="w-full text-white dark:text-white"
                        onClick={handleUpgradeToPro}
                        disabled={stripeLoading}
                      >
                        {stripeLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          'Upgrade to Pro'
                        )}
                      </Button>
                      <Button 
                        variant="outline" 
                        className="w-full dark:text-white dark:border-gray-600 dark:hover:bg-gray-700"
                        onClick={() => setActiveTab('subscription')}
                      >
                        View All Plans
                      </Button>
                    </div>
                  ) : (
                    <div className="space-y-3">
                      <p className="text-sm text-muted-foreground">
                        Manage your subscription and billing.
                      </p>
                      <Button 
                        variant="outline" 
                        className="w-full dark:text-white dark:border-gray-600 dark:hover:bg-gray-700"
                        onClick={handleManagePaymentMethod}
                        disabled={stripeLoading}
                      >
                        {stripeLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Loading...
                          </>
                        ) : (
                          'Update Payment Method'
                        )}
                      </Button>
                      <BillingHistoryModal onFetchBillingHistory={handleViewBillingHistory}>
                        <Button 
                          variant="outline" 
                          className="w-full dark:text-white dark:border-gray-600 dark:hover:bg-gray-700"
                          disabled={stripeLoading}
                        >
                          {stripeLoading ? (
                            <>
                              <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                              Loading...
                            </>
                          ) : (
                            'View Billing History'
                          )}
                        </Button>
                      </BillingHistoryModal>
                      <Button 
                        variant="destructive" 
                        className="w-full text-white dark:text-white"
                        onClick={handleCancelSubscription}
                        disabled={stripeLoading}
                      >
                        {stripeLoading ? (
                          <>
                            <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                            Processing...
                          </>
                        ) : (
                          'Cancel Subscription'
                        )}
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
                <SubscriptionPricing currentPlan={subscription?.plan} />
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

export default function ProfilePage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ProfilePageContent />
    </Suspense>
  )
}
