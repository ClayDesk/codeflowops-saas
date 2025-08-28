'use client'

import { useState, useEffect } from 'react'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { AlertTriangle, Clock, TrendingUp } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface QuotaWarningProps {
  beforeAction?: 'deploy' | 'analyze' | 'action'
  onCheckComplete?: (canProceed: boolean, reason?: string) => void
}

interface QuotaCheck {
  can_deploy: boolean
  checks: {
    monthly: { passed: boolean; reason: string }
    concurrent: { passed: boolean; reason: string }
  }
  quota_status: {
    plan: { tier: string; name: string }
    monthly_runs: { used: number; limit: number; percentage: number }
    concurrent_runs: { active: number; limit: number }
  }
}

export function QuotaWarning({ beforeAction = 'deploy', onCheckComplete }: QuotaWarningProps) {
  const [quotaCheck, setQuotaCheck] = useState<QuotaCheck | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const router = useRouter()

  useEffect(() => {
    checkQuota()
  }, [])

  const checkQuota = async () => {
    try {
      setLoading(true)
      const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com'
      
      // For now, default to free plan - in production, get from user context
      const response = await fetch(`${API_BASE}/api/quota/check?plan=free`, {
        method: 'POST',
        credentials: 'include'
      })
      
      if (response.ok) {
        const data = await response.json()
        setQuotaCheck(data)
        onCheckComplete?.(data.can_deploy, data.can_deploy ? undefined : getBlockReason(data))
      } else {
        setError('Failed to check quota limits')
        onCheckComplete?.(true) // Allow on error
      }
    } catch (err) {
      console.error('Quota check error:', err)
      setError('Failed to check quota limits')
      onCheckComplete?.(true) // Allow on error
    } finally {
      setLoading(false)
    }
  }

  const getBlockReason = (check: QuotaCheck): string => {
    if (!check.checks.monthly.passed) {
      return check.checks.monthly.reason
    }
    if (!check.checks.concurrent.passed) {
      return check.checks.concurrent.reason
    }
    return 'Unknown quota limit reached'
  }

  const handleUpgrade = () => {
    router.push('/profile?tab=billing')
  }

  if (loading) {
    return (
      <Alert>
        <Clock className="h-4 w-4 animate-spin" />
        <AlertDescription>Checking deployment limits...</AlertDescription>
      </Alert>
    )
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Warning: Could not verify quota limits. Proceeding may fail if limits are exceeded.
        </AlertDescription>
      </Alert>
    )
  }

  if (!quotaCheck) return null

  // Show warning if blocked or near limit
  const showWarning = !quotaCheck.can_deploy || quotaCheck.quota_status.monthly_runs.percentage >= 80

  if (!showWarning) return null

  return (
    <Alert variant={!quotaCheck.can_deploy ? "destructive" : "default"}>
      <AlertTriangle className="h-4 w-4" />
      <AlertDescription>
        <div className="space-y-3">
          {!quotaCheck.can_deploy ? (
            <>
              <div>
                <strong>🚫 {beforeAction.charAt(0).toUpperCase() + beforeAction.slice(1)} Blocked!</strong>
              </div>
              <div className="text-sm">
                {getBlockReason(quotaCheck)}
              </div>
              {!quotaCheck.checks.monthly.passed && (
                <div className="space-y-2">
                  <div className="text-xs text-gray-600">
                    Current plan: {quotaCheck.quota_status.plan.name} 
                    ({quotaCheck.quota_status.monthly_runs.used}/{quotaCheck.quota_status.monthly_runs.limit} deployments used)
                  </div>
                  <Button size="sm" onClick={handleUpgrade} className="w-full">
                    🚀 Upgrade for More Deployments
                  </Button>
                </div>
              )}
            </>
          ) : (
            <>
              <div>
                <strong>⚠️ Quota Warning!</strong>
              </div>
              <div className="text-sm">
                You've used {quotaCheck.quota_status.monthly_runs.percentage.toFixed(0)}% 
                of your monthly deployments ({quotaCheck.quota_status.monthly_runs.used}/{quotaCheck.quota_status.monthly_runs.limit}).
                {quotaCheck.quota_status.plan.tier === 'free' && ' Consider upgrading to avoid interruptions.'}
              </div>
              {quotaCheck.quota_status.plan.tier === 'free' && (
                <Button size="sm" variant="outline" onClick={handleUpgrade} className="w-full">
                  <TrendingUp className="h-4 w-4 mr-1" />
                  View Upgrade Options
                </Button>
              )}
            </>
          )}
        </div>
      </AlertDescription>
    </Alert>
  )
}
