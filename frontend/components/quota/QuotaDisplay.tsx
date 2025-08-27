'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { 
  Clock, 
  Activity, 
  TrendingUp, 
  AlertTriangle, 
  CheckCircle,
  Zap
} from 'lucide-react'

interface QuotaStatus {
  plan: {
    tier: string
    name: string
  }
  monthly_runs: {
    used: number
    limit: number | string
    remaining: number | string
    percentage: number
    unlimited: boolean
  }
  concurrent_runs: {
    active: number
    limit: number
    remaining: number
    percentage: number
  }
  deployment_allowed: {
    can_deploy: boolean
    monthly_check: {
      passed: boolean
      reason: string
    }
    concurrent_check: {
      passed: boolean
      reason: string
    }
  }
  upgrade_suggestion?: string
}

interface QuotaDisplayProps {
  onUpgrade?: () => void
}

export function QuotaDisplay({ onUpgrade }: QuotaDisplayProps) {
  const [quota, setQuota] = useState<QuotaStatus | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    fetchQuotaStatus()
  }, [])

  const fetchQuotaStatus = async () => {
    try {
      setLoading(true)
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
      const response = await fetch(`${API_BASE}/api/quota/status`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setQuota(data.quota)
      } else {
        setError('Failed to load quota information')
      }
    } catch (err) {
      console.error('Quota fetch error:', err)
      setError('Failed to load quota information')
    } finally {
      setLoading(false)
    }
  }

  const getStatusColor = (percentage: number) => {
    if (percentage >= 90) return 'text-red-600'
    if (percentage >= 70) return 'text-yellow-600'
    return 'text-green-600'
  }

  const getProgressColor = (percentage: number) => {
    if (percentage >= 90) return 'bg-red-500'
    if (percentage >= 70) return 'bg-yellow-500'
    return 'bg-green-500'
  }

  if (loading) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Usage & Limits</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="animate-pulse space-y-4">
            <div className="h-4 bg-gray-200 rounded w-3/4"></div>
            <div className="h-2 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !quota) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Usage & Limits</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>{error || 'Failed to load quota information'}</AlertDescription>
          </Alert>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Activity className="h-5 w-5" />
            <span>Usage & Limits</span>
          </div>
          <Badge variant="outline" className="capitalize">
            {quota.plan.name}
          </Badge>
        </CardTitle>
        <CardDescription>
          Track your deployment usage and plan limits
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        
        {/* Deployment Status Alert */}
        {!quota.deployment_allowed.can_deploy ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-2">
                <div>
                  <strong>⚠️ Deployments Blocked!</strong>
                </div>
                <div className="text-sm">
                  {!quota.deployment_allowed.monthly_check.passed 
                    ? `📅 ${quota.deployment_allowed.monthly_check.reason}`
                    : `⚡ ${quota.deployment_allowed.concurrent_check.reason}`
                  }
                </div>
                {!quota.deployment_allowed.monthly_check.passed && (
                  <Button 
                    size="sm" 
                    className="mt-2 w-full"
                    onClick={onUpgrade}
                  >
                    🚀 Upgrade for More Deployments
                  </Button>
                )}
              </div>
            </AlertDescription>
          </Alert>
        ) : quota.monthly_runs.percentage >= 80 ? (
          <Alert variant="destructive">
            <AlertTriangle className="h-4 w-4" />
            <AlertDescription>
              <div className="space-y-2">
                <div>
                  <strong>⚠️ Quota Warning!</strong>
                </div>
                <div className="text-sm">
                  You've used {quota.monthly_runs.percentage.toFixed(0)}% of your monthly deployments. 
                  Consider upgrading to avoid service interruption.
                </div>
                <Button 
                  size="sm" 
                  variant="outline"
                  className="mt-2 w-full"
                  onClick={onUpgrade}
                >
                  View Upgrade Options
                </Button>
              </div>
            </AlertDescription>
          </Alert>
        ) : (
          <Alert>
            <CheckCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>✅ Ready to deploy!</strong> All quota limits are within acceptable range.
            </AlertDescription>
          </Alert>
        )}

        {/* Monthly Runs */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Clock className="h-4 w-4 text-blue-600" />
              <span className="font-medium">Monthly Deployments</span>
            </div>
            <span className={`text-sm font-medium ${getStatusColor(quota.monthly_runs.percentage)}`}>
              {quota.monthly_runs.unlimited 
                ? `${quota.monthly_runs.used} used`
                : `${quota.monthly_runs.used} / ${quota.monthly_runs.limit}`
              }
            </span>
          </div>
          
          {!quota.monthly_runs.unlimited && (
            <Progress 
              value={quota.monthly_runs.percentage} 
              className="h-2"
            />
          )}
          
          <div className="flex justify-between text-xs text-gray-600">
            <span>
              {quota.monthly_runs.unlimited 
                ? 'Unlimited deployments'
                : `${quota.monthly_runs.remaining} remaining this month`
              }
            </span>
            {!quota.monthly_runs.unlimited && (
              <span className={getStatusColor(quota.monthly_runs.percentage)}>
                {quota.monthly_runs.percentage.toFixed(1)}%
              </span>
            )}
          </div>
        </div>

        {/* Concurrent Runs */}
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <Zap className="h-4 w-4 text-purple-600" />
              <span className="font-medium">Concurrent Deployments</span>
            </div>
            <span className={`text-sm font-medium ${getStatusColor(quota.concurrent_runs.percentage)}`}>
              {quota.concurrent_runs.active} / {quota.concurrent_runs.limit}
            </span>
          </div>
          
          <Progress 
            value={quota.concurrent_runs.percentage} 
            className="h-2"
          />
          
          <div className="flex justify-between text-xs text-gray-600">
            <span>
              {quota.concurrent_runs.remaining} slots available
            </span>
            <span className={getStatusColor(quota.concurrent_runs.percentage)}>
              {quota.concurrent_runs.percentage.toFixed(1)}%
            </span>
          </div>
        </div>

        {/* Upgrade Suggestions & Actions */}
        <div className="pt-4 border-t space-y-3">
          {quota.upgrade_suggestion ? (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium">💡 Recommendation</span>
              </div>
              <p className="text-sm text-gray-600">
                {quota.upgrade_suggestion}
              </p>
              <Button size="sm" onClick={onUpgrade} className="w-full">
                🚀 Upgrade Now
              </Button>
            </div>
          ) : quota.plan.tier === 'free' && quota.monthly_runs.percentage >= 50 ? (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium">💡 Growing Fast?</span>
              </div>
              <p className="text-sm text-gray-600">
                You're already at {quota.monthly_runs.percentage.toFixed(0)}% usage. 
                Starter plan gives you 50 deployments/month + 14-day free trial!
              </p>
              <Button size="sm" onClick={onUpgrade} className="w-full">
                🎯 Try Starter Free for 14 Days
              </Button>
            </div>
          ) : quota.plan.tier === 'starter' && quota.monthly_runs.percentage >= 60 ? (
            <div className="space-y-3">
              <div className="flex items-center space-x-2">
                <TrendingUp className="h-4 w-4 text-blue-600" />
                <span className="text-sm font-medium">🚀 Power User?</span>
              </div>
              <p className="text-sm text-gray-600">
                Pro plan offers 200 deployments/month + 5 concurrent deployments for teams.
              </p>
              <Button size="sm" onClick={onUpgrade} className="w-full">
                ⚡ Upgrade to Pro
              </Button>
            </div>
          ) : (
            <div className="text-center py-2">
              <Button 
                size="sm" 
                variant="outline" 
                onClick={onUpgrade}
                className="w-full"
              >
                📊 View All Plans
              </Button>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
