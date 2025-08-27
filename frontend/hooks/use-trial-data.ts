import { useState, useEffect } from 'react'

export interface TrialMetrics {
  trial_start: string
  trial_end: string
  days_remaining: number
  usage_percentage: number
  deployments_used: number
  deployments_limit: number
  engagement_score: number
  conversion_likelihood: number
}

export interface TrialWarning {
  type: string
  title: string
  message: string
  action: string
  urgency: string
}

export interface TrialRecommendation {
  type: string
  title: string
  description: string
  action: string
  priority: string
}

export interface TrialExtension {
  should_extend: boolean
  extension_days: number
  reason: string
}

export interface TrialData {
  metrics: TrialMetrics
  warnings: TrialWarning
  recommendations: TrialRecommendation[]
  extension: TrialExtension
  grace_period: boolean
}

export interface TrialResponse {
  success: boolean
  trial?: TrialData
  error?: string
}

export function useTrialData() {
  const [trial, setTrial] = useState<TrialData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchTrialData = async () => {
    try {
      setLoading(true)
      const API_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'https://api.codeflowops.com'
      const response = await fetch(`${API_BASE}/api/trial/status`, {
        credentials: 'include'
      })
      
      if (response.ok) {
        const data: TrialResponse = await response.json()
        if (data.success && data.trial) {
          setTrial(data.trial)
          setError(null)
        } else {
          setError(data.error || 'Failed to load trial data')
        }
      } else {
        setError('Failed to load trial data')
      }
    } catch (err) {
      console.error('Trial fetch error:', err)
      setError('Failed to load trial data')
    } finally {
      setLoading(false)
    }
  }

  const extendTrial = async (days: number, reason?: string): Promise<boolean> => {
    try {
      const API_BASE = typeof window !== 'undefined' && window.location.hostname === 'localhost'
        ? 'http://localhost:8000'
        : 'https://api.codeflowops.com'
      const response = await fetch(`${API_BASE}/api/trial/extend`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ days, reason })
      })
      
      if (response.ok) {
        const data = await response.json()
        if (data.success) {
          // Refresh trial data
          await fetchTrialData()
          return true
        }
      }
      return false
    } catch (err) {
      console.error('Trial extension error:', err)
      return false
    }
  }

  useEffect(() => {
    fetchTrialData()
  }, [])

  return {
    trial,
    loading,
    error,
    refetch: fetchTrialData,
    extendTrial
  }
}

export default useTrialData
