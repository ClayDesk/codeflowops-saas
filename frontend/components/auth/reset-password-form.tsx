'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Loader2, Lock, Eye, EyeOff, AlertCircle, CheckCircle, Mail } from 'lucide-react'

export function ResetPasswordForm() {
  const [email, setEmail] = useState('')
  const [verificationCode, setVerificationCode] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [step, setStep] = useState<'email' | 'reset'>('email')

  const router = useRouter()

  const validatePassword = () => {
    if (newPassword.length < 8) {
      setError('Password must be at least 8 characters long')
      return false
    }

    // AWS Cognito default password policy
    const hasUpperCase = /[A-Z]/.test(newPassword)
    const hasLowerCase = /[a-z]/.test(newPassword)
    const hasNumbers = /\d/.test(newPassword)
    const hasSpecialChar = /[!@#$%^&*(),.?":{}|<>]/.test(newPassword)

    if (!(hasUpperCase && hasLowerCase && hasNumbers && hasSpecialChar)) {
      setError('Password must contain at least one uppercase letter, lowercase letter, number, and special character')
      return false
    }

    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      return false
    }

    return true
  }

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    if (!email.trim()) {
      setError('Please enter your email address')
      setIsLoading(false)
      return
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
      
      const response = await fetch(`${API_BASE}/api/v1/auth/forgot-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email: email.trim() }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Password reset request failed' }))
        throw new Error(errorData.detail || 'Password reset request failed')
      }

      setStep('reset')

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Password reset request failed. Please try again.'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    if (!verificationCode.trim()) {
      setError('Please enter the verification code')
      setIsLoading(false)
      return
    }

    if (!validatePassword()) {
      setIsLoading(false)
      return
    }

    try {
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
      
      const response = await fetch(`${API_BASE}/api/v1/auth/confirm-reset-password`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          email: email.trim(),
          token: verificationCode.trim(),
          new_password: newPassword,
        }),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Password reset failed' }))
        throw new Error(errorData.detail || 'Password reset failed')
      }

      setSuccess(true)
      
      // Redirect to login after 3 seconds
      setTimeout(() => {
        router.push('/login?message=Password reset successful. Please log in with your new password.')
      }, 3000)

    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Password reset failed. Please try again.'
      setError(errorMessage)
    } finally {
      setIsLoading(false)
    }
  }

  const getPasswordStrength = () => {
    if (!newPassword) return { strength: 0, text: '', color: 'bg-gray-200' }
    
    let strength = 0
    const checks = [
      newPassword.length >= 8,
      /[A-Z]/.test(newPassword),
      /[a-z]/.test(newPassword),
      /\d/.test(newPassword),
      /[!@#$%^&*(),.?":{}|<>]/.test(newPassword)
    ]
    
    strength = checks.filter(Boolean).length
    
    const strengthTexts = ['Very Weak', 'Weak', 'Fair', 'Good', 'Strong']
    const strengthColors = ['bg-red-500', 'bg-orange-500', 'bg-yellow-500', 'bg-blue-500', 'bg-green-500']
    
    return {
      strength,
      text: strengthTexts[strength - 1] || '',
      color: strengthColors[strength - 1] || 'bg-gray-200'
    }
  }

  const passwordStrength = getPasswordStrength()

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900 py-12 px-4 sm:px-6 lg:px-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl font-bold text-center">
            {step === 'email' ? 'Reset Your Password' : 'Enter Verification Code'}
          </CardTitle>
          <CardDescription className="text-center">
            {step === 'email' 
              ? 'Enter your email address to receive a reset code'
              : 'Check your email for a 6-digit verification code'
            }
          </CardDescription>
        </CardHeader>

        <CardContent>
          {success ? (
            <div className="space-y-4">
              <Alert>
                <CheckCircle className="h-4 w-4" />
                <AlertDescription>
                  Your password has been successfully reset! You will be redirected to the login page shortly.
                </AlertDescription>
              </Alert>
            </div>
          ) : step === 'email' ? (
            <form onSubmit={handleRequestReset} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="space-y-2">
                <Label htmlFor="email">Email Address</Label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    className="pl-10"
                    disabled={isLoading}
                  />
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
                    Sending Reset Code...
                  </>
                ) : (
                  'Send Reset Code'
                )}
              </Button>
            </form>
          ) : (
            <form onSubmit={handleResetPassword} className="space-y-4">
              {error && (
                <Alert variant="destructive">
                  <AlertCircle className="h-4 w-4" />
                  <AlertDescription>{error}</AlertDescription>
                </Alert>
              )}

              <div className="mb-4">
                <Alert>
                  <Mail className="h-4 w-4" />
                  <AlertDescription>
                    A 6-digit verification code has been sent to <strong>{email}</strong>.
                    Please check your email (including spam folder).
                  </AlertDescription>
                </Alert>
              </div>

              <div className="space-y-2">
                <Label htmlFor="verificationCode">Verification Code</Label>
                <Input
                  id="verificationCode"
                  type="text"
                  placeholder="Enter 6-digit code"
                  value={verificationCode}
                  onChange={(e) => setVerificationCode(e.target.value.replace(/\D/g, '').slice(0, 6))}
                  required
                  className="text-center text-lg tracking-widest"
                  disabled={isLoading}
                  maxLength={6}
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="newPassword">New Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="newPassword"
                    type={showPassword ? 'text' : 'password'}
                    placeholder="Enter your new password"
                    value={newPassword}
                    onChange={(e) => setNewPassword(e.target.value)}
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
                
                {newPassword && (
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
                <Label htmlFor="confirmPassword">Confirm New Password</Label>
                <div className="relative">
                  <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 h-4 w-4" />
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? 'text' : 'password'}
                    placeholder="Confirm your new password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
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

              <div className="flex space-x-2">
                <Button
                  type="button"
                  variant="outline"
                  onClick={() => setStep('email')}
                  disabled={isLoading}
                  className="w-full"
                >
                  Back
                </Button>
                <Button
                  type="submit"
                  className="w-full"
                  disabled={isLoading}
                >
                  {isLoading ? (
                    <>
                      <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                      Resetting...
                    </>
                  ) : (
                    'Reset Password'
                  )}
                </Button>
              </div>
            </form>
          )}
        </CardContent>

        <CardFooter className="flex justify-center">
          {!success && (
            <div className="text-sm text-center text-muted-foreground">
              Remember your password?{' '}
              <Link href="/login" className="text-primary hover:underline">
                Back to login
              </Link>
            </div>
          )}
        </CardFooter>
      </Card>
    </div>
  )
}
