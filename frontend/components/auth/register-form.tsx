'use client'

import { useState, useEffect } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Mail, Lock, User, Eye, EyeOff, CheckCircle, CreditCard, Clock } from 'lucide-react'

interface RegisterFormProps {
  redirectTo?: string
}

export function RegisterForm({ redirectTo = '/deploy' }: RegisterFormProps) {
  const [formData, setFormData] = useState({
    username: '',
    email: '',
    password: '',
    confirmPassword: '',
    full_name: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [planInfo, setPlanInfo] = useState<{
    plan: string | null
    trial: string | null
    redirect: string | null
  }>({ plan: null, trial: null, redirect: null })

  const { register } = useAuth()
  const router = useRouter()
  const searchParams = useSearchParams()

  // Extract plan parameters from URL
  useEffect(() => {
    const plan = searchParams.get('plan')
    const trial = searchParams.get('trial')
    const redirect = searchParams.get('redirect')
    
    if (plan) {
      setPlanInfo({ plan, trial, redirect })
    }
  }, [searchParams])

  // Helper function to get plan details
  const getPlanDetails = (planName: string) => {
    const plans: Record<string, { name: string; price: string; trialDays?: number }> = {
      starter: { name: 'Starter Plan', price: '$19/month', trialDays: 14 },
      pro: { name: 'Pro Plan', price: '$49/month', trialDays: 7 },
      free: { name: 'Free Plan', price: 'Free forever' }
    }
    return plans[planName.toLowerCase()] || null
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const validateForm = () => {
    setError('')
    
    // Username validation
    if (!formData.username.trim()) {
      setError('Username is required')
      return false
    }
    
    if (formData.username.length < 3) {
      setError('Username must be at least 3 characters long')
      return false
    }
    
    // Email validation
    if (!formData.email.trim()) {
      setError('Email is required')
      return false
    }
    
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/
    if (!emailRegex.test(formData.email)) {
      setError('Please enter a valid email address')
      return false
    }
    
    // Password validation - AWS Cognito requirements
    if (!formData.password) {
      setError('Password is required')
      return false
    }
    
    if (formData.password.length < 8) {
      setError('Password must be at least 8 characters long')
      return false
    }

    // AWS Cognito default password policy
    const hasUpperCase = /[A-Z]/.test(formData.password)
    const hasLowerCase = /[a-z]/.test(formData.password)
    const hasNumbers = /\d/.test(formData.password)
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(formData.password)

    if (!(hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar)) {
      setError('Password must contain at least one uppercase letter, lowercase letter, number, and special character')
      return false
    }

    // Confirm password validation
    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      return false
    }

    // Name validation (optional but if provided should be valid)
    if (formData.full_name && formData.full_name.trim().length < 2) {
      setError('Full name must be at least 2 characters long')
      return false
    }

    return true
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    setSuccess('')

    if (!validateForm()) {
      setIsLoading(false)
      return
    }

    try {
      await register({
        username: formData.username.trim(),
        email: formData.email.trim(),
        password: formData.password,
        full_name: formData.full_name?.trim() || undefined
      })
      
      setSuccess('Account created successfully! You are now logged in.')
      
      // Clear the form
      setFormData({
        username: '',
        email: '',
        password: '',
        confirmPassword: '',
        full_name: ''
      })
      
      // If user was registering for a specific plan, trigger subscription
      if (planInfo.plan && planInfo.plan !== 'free') {
        setSuccess('Account created! Setting up your subscription...')
        
        setTimeout(async () => {
          try {
            // Trigger subscription flow
            const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
            const response = await fetch(`${API_BASE}/api/v1/billing/subscribe/${planInfo.plan}`, {
              method: 'POST',
              headers: {
                'Content-Type': 'application/json',
              },
              credentials: 'include'
            })

            if (response.ok) {
              const data = await response.json()
              if (data.checkout_url) {
                window.location.href = data.checkout_url
                return
              }
            }
            
            // Fallback: redirect to profile for manual subscription
            router.push('/profile?tab=billing')
          } catch (err) {
            console.error('Subscription setup failed:', err)
            // Still redirect to profile where user can manually subscribe
            router.push('/profile?tab=billing')
          }
        }, 1500)
      } else {
        // Regular redirect without subscription
        setTimeout(() => {
          router.push(planInfo.redirect || redirectTo)
        }, 1500)
      }
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Registration failed. Please try again.'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const getPasswordStrength = () => {
    const { password } = formData
    if (!password) return { strength: 0, text: '' }
    
    let strength = 0
    const checks = [
      password.length >= 8,
      /[A-Z]/.test(password),
      /[a-z]/.test(password),
      /\d/.test(password),
      /[!@#$%^&*(),.?":{}|<>]/.test(password)
    ]
    
    strength = checks.filter(Boolean).length
    
    const strengthTexts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
    const colors = ['bg-red-500', 'bg-red-400', 'bg-yellow-500', 'bg-blue-500', 'bg-green-500']
    
    return {
      strength,
      text: strengthTexts[strength - 1] || '',
      color: colors[strength - 1] || 'bg-gray-200'
    }
  }

  const passwordStrength = getPasswordStrength()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">Create Account</CardTitle>
          <CardDescription className="text-center">
            {planInfo.plan ? `Sign up for CodeFlowOps ${getPlanDetails(planInfo.plan)?.name}` : 'Sign up for CodeFlowOps to get started'}
          </CardDescription>
        </CardHeader>

        <CardContent>
          {/* Plan Information Display */}
          {planInfo.plan && getPlanDetails(planInfo.plan) && (
            <div className="mb-6 p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="flex items-center space-x-2 mb-2">
                <CreditCard className="h-5 w-5 text-blue-600" />
                <h3 className="font-semibold text-blue-900 dark:text-blue-100">
                  {getPlanDetails(planInfo.plan)?.name}
                </h3>
              </div>
              <div className="text-sm text-blue-800 dark:text-blue-200">
                <p className="font-medium">{getPlanDetails(planInfo.plan)?.price}</p>
                {planInfo.trial === 'true' && getPlanDetails(planInfo.plan)?.trialDays && (
                  <div className="flex items-center space-x-1 mt-1">
                    <Clock className="h-4 w-4" />
                    <span>{getPlanDetails(planInfo.plan)?.trialDays}-day free trial included</span>
                  </div>
                )}
                <p className="mt-2 text-xs">
                  After creating your account, you'll be redirected to complete your subscription setup.
                </p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            {success && (
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>{success}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Username *</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  id="username"
                  name="username"
                  type="text"
                  placeholder="Choose a username"
                  value={formData.username}
                  onChange={handleInputChange}
                  required
                  className="pl-10"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="full_name">Full Name (Optional)</Label>
              <div className="relative">
                <User className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  id="full_name"
                  name="full_name"
                  type="text"
                  placeholder="Enter your full name"
                  value={formData.full_name}
                  onChange={handleInputChange}
                  className="pl-10"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="email">Email *</Label>
              <div className="relative">
                <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  id="email"
                  name="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={handleInputChange}
                  required
                  className="pl-10"
                  disabled={isLoading}
                />
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password *</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  id="password"
                  name="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Create a password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  className="pl-10 pr-10"
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowPassword(!showPassword)}
                  disabled={isLoading}
                >
                  {showPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </Button>
              </div>
              
              {formData.password && (
                <div className="space-y-1">
                  <div className="flex justify-between text-xs">
                    <span>Password strength:</span>
                    <span className={passwordStrength.strength >= 4 ? 'text-green-600' : 'text-gray-500'}>
                      {passwordStrength.text}
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 rounded-full h-2">
                    <div 
                      className={`h-2 rounded-full transition-all ${passwordStrength.color}`}
                      style={{ width: `${(passwordStrength.strength / 5) * 100}%` }}
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Confirm Password *</Label>
              <div className="relative">
                <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                <Input
                  id="confirmPassword"
                  name="confirmPassword"
                  type={showConfirmPassword ? 'text' : 'password'}
                  placeholder="Confirm your password"
                  value={formData.confirmPassword}
                  onChange={handleInputChange}
                  required
                  className="pl-10 pr-10"
                  disabled={isLoading}
                />
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  className="absolute right-0 top-0 h-full px-3 py-2 hover:bg-transparent"
                  onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                  disabled={isLoading}
                >
                  {showConfirmPassword ? (
                    <EyeOff className="h-4 w-4 text-gray-400" />
                  ) : (
                    <Eye className="h-4 w-4 text-gray-400" />
                  )}
                </Button>
              </div>
            </div>

            <Button
              type="submit"
              className="w-full"
              disabled={isLoading}
            >
              {isLoading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  Creating account...
                </>
              ) : (
                'Create Account'
              )}
            </Button>

            {/* GitHub Login Section */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">
                  Or continue with
                </span>
              </div>
            </div>

            <Button
              type="button"
              variant="outline"
              className="w-full"
              onClick={() => {
                const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
                window.location.href = `${API_BASE}/api/v1/auth/github`
              }}
              disabled={isLoading}
            >
              <span className="mr-2 text-lg">⚡</span>
              Continue with GitHub
            </Button>
          </form>
        </CardContent>

        <CardFooter className="flex flex-col space-y-2">
          <div className="text-sm text-center text-muted-foreground">
            Already have an account?{' '}
            <Link href="/login" className="text-primary hover:underline">
              Sign in
            </Link>
          </div>
          <div className="text-xs text-center text-muted-foreground">
            By creating an account, you agree to our Terms of Service and Privacy Policy.
          </div>
        </CardFooter>
      </Card>
    </div>
  )
}
