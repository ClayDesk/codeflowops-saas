'use client'

import React, { useState, useEffect, Suspense } from 'react'
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
  Mail, 
  Shield, 
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
  const [isLoading, setIsLoading] = useState(true)
  const [isEditing, setIsEditing] = useState(false)
  const [deployments, setDeployments] = useState<Deployment[]>([])
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
  }, [isAuthenticated, fetchUserProfile, fetchUserDeployments])

  // Handle tab selection from URL parameters
  useEffect(() => {
    const tab = searchParams.get('tab')
    if (tab && ['overview', 'deployments', 'settings'].includes(tab)) {
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
        const deploymentsResponse = await fetchUserDeployments() as { deployments?: Deployment[] }
        if (deploymentsResponse?.deployments) {
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
          <TabsList className="grid w-full grid-cols-3">
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="deployments">Deployments</TabsTrigger>
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
                      You haven&apos;t deployed anything in the last 7 days.
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
