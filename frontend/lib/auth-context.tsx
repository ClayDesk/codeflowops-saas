'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'

// Types
export interface User {
  id: string
  email: string
  name?: string
  username?: string
  full_name?: string
  provider: string
}

export interface AuthState {
  user: User | null
  loading: boolean
  isAuthenticated: boolean
}

export interface LoginData {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  full_name?: string
}

export interface AuthResponse {
  access_token: string
  refresh_token?: string
  token_type: string
  expires_in: number
  user: User
}

export interface CognitoConfig {
  region: string
  userPoolId: string
  clientId: string
  domain?: string
  redirectUri?: string
}

export interface AuthError {
  code: string
  message: string
  details?: string
}

interface AuthContextType extends AuthState {
  login: (data: LoginData) => Promise<void>
  register: (data: RegisterData) => Promise<void>
  logout: () => Promise<void>
  refreshToken: () => Promise<void>
  getCognitoConfig: () => Promise<CognitoConfig | null>
  resetPassword: (email: string) => Promise<void>
  fetchUserProfile: () => Promise<any>
  updateUserProfile: (profileData: any) => Promise<any>
  fetchUserDeployments: () => Promise<any>
  clearDeploymentHistory: () => Promise<any>
  profilePicture: string | null
  updateProfilePicture: (imageFile: File) => Promise<void>
  removeProfilePicture: () => void
}

// Create context
const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Auth provider component
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [profilePicture, setProfilePicture] = useState<string | null>(null)
  const router = useRouter()

  const isAuthenticated = !!user

  // API base URL
  const API_BASE = process.env.NEXT_PUBLIC_API_URL || process.env.REACT_APP_API_URL || 'http://localhost:8000'

  // Storage keys
  const ACCESS_TOKEN_KEY = 'codeflowops_access_token'
  const REFRESH_TOKEN_KEY = 'codeflowops_refresh_token'
  const USER_KEY = 'codeflowops_user'

  // Utility function for better error handling
  const parseAuthError = (error: any): AuthError => {
    if (typeof error === 'string') {
      return { code: 'UNKNOWN_ERROR', message: error }
    }
    
    if (error?.detail) {
      // Backend error format
      if (typeof error.detail === 'string') {
        // Check for Cognito-specific errors
        if (error.detail.includes('Auth flow not enabled')) {
          return {
            code: 'COGNITO_AUTH_FLOW_ERROR',
            message: 'Authentication method not configured properly',
            details: 'Please contact support - authentication service needs configuration'
          }
        }
        if (error.detail.includes('User does not exist') || error.detail.includes('Incorrect username or password')) {
          return {
            code: 'INVALID_CREDENTIALS',
            message: 'Invalid email or password'
          }
        }
        if (error.detail.includes('User already exists')) {
          return {
            code: 'USER_EXISTS',
            message: 'An account with this email already exists'
          }
        }
        if (error.detail.includes('Password does not conform to policy')) {
          return {
            code: 'WEAK_PASSWORD',
            message: 'Password does not meet requirements',
            details: 'Password must contain uppercase, lowercase, number and special character'
          }
        }
        return { code: 'API_ERROR', message: error.detail }
      }
    }
    
    return {
      code: 'NETWORK_ERROR',
      message: error?.message || 'Network error occurred'
    }
  }

  // Helper functions
  const getStoredToken = () => {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(ACCESS_TOKEN_KEY)
  }

  const getStoredRefreshToken = () => {
    if (typeof window === 'undefined') return null
    return localStorage.getItem(REFRESH_TOKEN_KEY)
  }

  const getStoredUser = (): User | null => {
    if (typeof window === 'undefined') return null
    const stored = localStorage.getItem(USER_KEY)
    return stored ? JSON.parse(stored) : null
  }

  const storeAuthData = (authData: AuthResponse) => {
    if (typeof window === 'undefined') return
    
    localStorage.setItem(ACCESS_TOKEN_KEY, authData.access_token)
    if (authData.refresh_token) {
      localStorage.setItem(REFRESH_TOKEN_KEY, authData.refresh_token)
    }
    localStorage.setItem(USER_KEY, JSON.stringify(authData.user))
    setUser(authData.user)
  }

  const clearAuthData = () => {
    if (typeof window === 'undefined') return
    
    localStorage.removeItem(ACCESS_TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setUser(null)
  }

  // API functions with enhanced error handling
  const login = async (data: LoginData): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Login failed' }))
        const authError = parseAuthError(errorData)
        throw new Error(authError.message)
      }

      const authData: AuthResponse = await response.json()
      storeAuthData(authData)
    } catch (error) {
      console.error('Login error:', error)
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Login failed due to network error')
    }
  }

  const register = async (data: RegisterData): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(data),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Registration failed' }))
        const authError = parseAuthError(errorData)
        throw new Error(authError.message)
      }

      const authData: AuthResponse = await response.json()
      storeAuthData(authData)
    } catch (error) {
      console.error('Registration error:', error)
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Registration failed due to network error')
    }
  }

  const getCognitoConfig = async (): Promise<CognitoConfig | null> => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/config`)
      if (!response.ok) {
        return null
      }
      const config = await response.json()
      return {
        region: config.cognito?.region || 'us-east-1',
        userPoolId: config.cognito?.userPoolId || '',
        clientId: config.cognito?.clientId || '',
        domain: config.cognito?.domain,
        redirectUri: config.cognito?.redirectUri
      }
    } catch (error) {
      console.error('Failed to get Cognito config:', error)
      return null
    }
  }

  const resetPassword = async (email: string): Promise<void> => {
    try {
      const response = await fetch(`${API_BASE}/api/v1/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Password reset failed' }))
        const authError = parseAuthError(errorData)
        throw new Error(authError.message)
      }
    } catch (error) {
      console.error('Password reset error:', error)
      if (error instanceof Error) {
        throw error
      }
      throw new Error('Password reset failed due to network error')
    }
  }

  const logout = async (): Promise<void> => {
    try {
      // Check if user is authenticated via GitHub
      if (user?.provider === 'github') {
        await fetch(`${API_BASE}/auth/github/logout`, {
          method: 'POST',
          credentials: 'include', // Include cookies
        })
      } else {
        // Traditional token-based logout
        const token = getStoredToken()
        if (token) {
          await fetch(`${API_BASE}/api/v1/auth/logout`, {
            method: 'POST',
            headers: {
              'Authorization': `Bearer ${token}`,
            },
          })
        }
      }
    } catch (error) {
      console.error('Logout error:', error)
    } finally {
      clearAuthData()
      router.push('/login')
    }
  }

  // Fetch user profile data
  const fetchUserProfile = async () => {
    try {
      const token = getStoredToken()
      if (!token) {
        throw new Error('No access token found')
      }

      const response = await fetch(`${API_BASE}/api/v1/auth/profile`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch profile')
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching profile:', error)
      throw error
    }
  }

  // Update user profile
  const updateUserProfile = async (profileData: any) => {
    try {
      const token = getStoredToken()
      if (!token) {
        throw new Error('No access token found')
      }

      const response = await fetch(`${API_BASE}/api/v1/auth/profile`, {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(profileData),
      })

      if (!response.ok) {
        throw new Error('Failed to update profile')
      }

      const data = await response.json()
      // Update local user state
      setUser(data.user)
      return data
    } catch (error) {
      console.error('Error updating profile:', error)
      throw error
    }
  }

  // Fetch user deployments
  const fetchUserDeployments = async () => {
    try {
      const token = getStoredToken()
      if (!token) {
        throw new Error('No access token found')
      }

      const response = await fetch(`${API_BASE}/api/v1/auth/deployments`, {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to fetch deployments')
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error fetching deployments:', error)
      throw error
    }
  }

  // Clear user deployment history
  const clearDeploymentHistory = async () => {
    try {
      const token = getStoredToken()
      if (!token) {
        throw new Error('No access token found')
      }

      const response = await fetch(`${API_BASE}/api/v1/auth/deployments/clear`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      })

      if (!response.ok) {
        throw new Error('Failed to clear deployment history')
      }

      const data = await response.json()
      return data
    } catch (error) {
      console.error('Error clearing deployment history:', error)
      throw error
    }
  }

  // Helper function to resize image and convert to base64
  const resizeImage = (file: File, maxWidth: number = 200, maxHeight: number = 200, quality: number = 0.8): Promise<string> => {
    return new Promise((resolve, reject) => {
      const canvas = document.createElement('canvas')
      const ctx = canvas.getContext('2d')
      const img = new Image()

      img.onload = () => {
        // Calculate new dimensions
        let { width, height } = img
        
        if (width > height) {
          if (width > maxWidth) {
            height = (height * maxWidth) / width
            width = maxWidth
          }
        } else {
          if (height > maxHeight) {
            width = (width * maxHeight) / height
            height = maxHeight
          }
        }

        // Set canvas dimensions
        canvas.width = width
        canvas.height = height

        // Draw and resize image
        ctx?.drawImage(img, 0, 0, width, height)

        // Convert to base64
        const resizedBase64 = canvas.toDataURL('image/jpeg', quality)
        resolve(resizedBase64)
      }

      img.onerror = () => reject(new Error('Failed to load image'))
      img.src = URL.createObjectURL(file)
    })
  }

  // Update profile picture
  const updateProfilePicture = async (imageFile: File) => {
    try {
      // Validate file type
      if (!imageFile.type.startsWith('image/')) {
        throw new Error('Please select a valid image file.')
      }

      // Validate file size (max 5MB)
      if (imageFile.size > 5 * 1024 * 1024) {
        throw new Error('Please select an image smaller than 5MB.')
      }

      // Resize image to optimize for avatar display
      const resizedImage = await resizeImage(imageFile, 200, 200, 0.8)
      
      // Update state
      setProfilePicture(resizedImage)
      
      // Store in localStorage with user-specific key
      if (user?.id) {
        localStorage.setItem(`profile_picture_${user.id}`, resizedImage)
      }
      
      console.log('Profile picture updated successfully')
    } catch (error) {
      console.error('Error updating profile picture:', error)
      throw error
    }
  }

  // Remove profile picture
  const removeProfilePicture = () => {
    setProfilePicture(null)
    
    // Remove from localStorage
    if (user?.id) {
      localStorage.removeItem(`profile_picture_${user.id}`)
    }
    
    console.log('Profile picture removed successfully')
  }

  // Load profile picture from localStorage when user changes
  useEffect(() => {
    if (user?.id) {
      const savedPicture = localStorage.getItem(`profile_picture_${user.id}`)
      if (savedPicture) {
        setProfilePicture(savedPicture)
      } else {
        setProfilePicture(null)
      }
    } else {
      setProfilePicture(null)
    }
  }, [user?.id])

  const refreshToken = async (): Promise<void> => {
    try {
      const refreshTokenValue = getStoredRefreshToken()
      if (!refreshTokenValue) {
        throw new Error('No refresh token available')
      }

      const response = await fetch(`${API_BASE}/api/v1/auth/refresh`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ refresh_token: refreshTokenValue }),
      })

      if (!response.ok) {
        throw new Error('Token refresh failed')
      }

      const authData: AuthResponse = await response.json()
      storeAuthData(authData)
    } catch (error) {
      console.error('Token refresh error:', error)
      clearAuthData()
      router.push('/login')
    }
  }

  // Function to check GitHub authentication
  const checkGitHubAuth = async (): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/auth/github/user`, {
        credentials: 'include', // Include cookies
      })

      if (response.ok) {
        const data = await response.json()
        if (data.authenticated && data.user) {
          setUser({
            id: data.user.id,
            email: data.user.email,
            name: data.user.name || data.user.login,
            username: data.user.login,
            provider: 'github'
          })
          return true
        }
      }
      return false
    } catch (error) {
      console.error('GitHub auth check error:', error)
      return false
    }
  }

  // Initialize auth state
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        // First check if user has GitHub authentication
        const hasGitHubAuth = await checkGitHubAuth()
        
        if (!hasGitHubAuth) {
          // Fallback to traditional token authentication
          const storedUser = getStoredUser()
          const token = getStoredToken()

          if (storedUser && token) {
            // Verify token is still valid
            const response = await fetch(`${API_BASE}/api/health`, {
              headers: {
                'Authorization': `Bearer ${token}`,
              },
            })

            if (response.ok) {
              setUser(storedUser)
            } else if (response.status === 401) {
              // Try to refresh token
              try {
                await refreshToken()
              } catch {
                clearAuthData()
              }
            } else {
              clearAuthData()
            }
          }
        }
      } catch (error) {
        console.error('Auth initialization error:', error)
        clearAuthData()
      } finally {
        setLoading(false)
      }
    }

    initializeAuth()
  }, [])

  const value: AuthContextType = {
    user,
    loading,
    isAuthenticated,
    login,
    register,
    logout,
    refreshToken,
    getCognitoConfig,
    resetPassword,
    fetchUserProfile,
    updateUserProfile,
    fetchUserDeployments,
    clearDeploymentHistory,
    profilePicture,
    updateProfilePicture,
    removeProfilePicture,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

// Hook to use auth context
export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

// Hook for protected routes
export function useRequireAuth() {
  const auth = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!auth.loading && !auth.isAuthenticated) {
      router.push('/login')
    }
  }, [auth.loading, auth.isAuthenticated, router])

  return auth
}
