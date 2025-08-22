/**
 * Billing Data Hook
 * Fetches real billing data from enterprise backend API
 */
'use client'

import { useState, useEffect } from 'react'

interface BillingPlan {
  name: string
  price: number
  currency: string
  billingCycle: 'monthly' | 'yearly'
  features: string[]
  limits: {
    deployments: number
    bandwidth: number
    storage: number
    domains: number
  }
}

interface UsageData {
  deployments: { used: number; limit: number }
  bandwidth: { used: number; limit: number; unit: string }
  storage: { used: number; limit: number; unit: string }
  domains: { used: number; limit: number }
}

interface BillingDataState {
  currentPlan: BillingPlan
  usage: UsageData
  currentBill: {
    amount: number
    currency: string
    period: string
    dueDate: string
    status: string
  }
  billingHistory: Array<{
    id: string
    date: string
    amount: number
    status: string
    description: string
  }>
  isLoading: boolean
  error: string | null
}

export function useBillingData() {
  const [data, setData] = useState<BillingDataState>({
    currentPlan: {
      name: 'Starter',
      price: 0,
      currency: 'USD', 
      billingCycle: 'monthly',
      features: ['Basic deployments', 'Community support'],
      limits: {
        deployments: 3,
        bandwidth: 10,
        storage: 5,
        domains: 1
      }
    },
    usage: {
      deployments: { used: 0, limit: 3 },
      bandwidth: { used: 0, limit: 10, unit: 'GB' },
      storage: { used: 0, limit: 5, unit: 'GB' },
      domains: { used: 0, limit: 1 }
    },
    currentBill: {
      amount: 0,
      currency: 'USD',
      period: new Date().toLocaleDateString('en-US', { month: 'long', year: 'numeric' }),
      dueDate: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString(),
      status: 'current'
    },
    billingHistory: [],
    isLoading: false,
    error: null
  })

  const fetchBillingData = async () => {
    try {
      setData(prev => ({ ...prev, isLoading: true, error: null }))

      // Test backend health first
      const healthResponse = await fetch('http://localhost:8000/health')
      if (!healthResponse.ok) {
        throw new Error('Backend not available')
      }

      // Fetch billing data from enterprise endpoints
      const [subscriptionResponse, usageResponse, billingResponse] = await Promise.all([
        fetch('http://localhost:8000/api/billing/subscription'),
        fetch('http://localhost:8000/api/billing/usage'),
        fetch('http://localhost:8000/api/billing/history')
      ])

      let planData = data.currentPlan
      let usageData = data.usage
      let billingHistory: any[] = []
      let currentBill = data.currentBill

      // Process subscription data
      if (subscriptionResponse.ok) {
        const subData = await subscriptionResponse.json()
        if (subData.success && subData.subscription) {
          planData = {
            name: subData.subscription.tier || 'Starter',
            price: subData.subscription.price || 0,
            currency: subData.subscription.currency || 'USD',
            billingCycle: subData.subscription.billing_cycle || 'monthly',
            features: subData.subscription.features || ['Basic deployments'],
            limits: subData.subscription.limits || {
              deployments: 3,
              bandwidth: 10,
              storage: 5,
              domains: 1
            }
          }
        }
      }

      // Process usage data
      if (usageResponse.ok) {
        const usage = await usageResponse.json()
        if (usage.success && usage.usage) {
          usageData = {
            deployments: {
              used: usage.usage.deployments_used || 0,
              limit: usage.usage.deployments_limit || planData.limits.deployments
            },
            bandwidth: {
              used: usage.usage.bandwidth_used || 0,
              limit: usage.usage.bandwidth_limit || planData.limits.bandwidth,
              unit: 'GB'
            },
            storage: {
              used: usage.usage.storage_used || 0,
              limit: usage.usage.storage_limit || planData.limits.storage,
              unit: 'GB'
            },
            domains: {
              used: usage.usage.domains_used || 0,
              limit: usage.usage.domains_limit || planData.limits.domains
            }
          }

          // Update current bill if available
          if (usage.current_bill) {
            currentBill = {
              amount: usage.current_bill.amount || 0,
              currency: usage.current_bill.currency || 'USD',
              period: usage.current_bill.period || currentBill.period,
              dueDate: usage.current_bill.due_date || currentBill.dueDate,
              status: usage.current_bill.status || 'current'
            }
          }
        }
      }

      // Process billing history
      if (billingResponse.ok) {
        const historyData = await billingResponse.json()
        if (historyData.success && historyData.bills) {
          billingHistory = historyData.bills.map((bill: any) => ({
            id: bill.id || bill.bill_id,
            date: bill.date || bill.created_at,
            amount: bill.amount || 0,
            status: bill.status || 'paid',
            description: bill.description || `${planData.name} subscription`
          }))
        }
      }

      setData({
        currentPlan: planData,
        usage: usageData,
        currentBill,
        billingHistory,
        isLoading: false,
        error: null
      })

    } catch (error) {
      console.error('Failed to fetch billing data:', error)
      
      setData(prev => ({
        ...prev,
        isLoading: false,
        error: error instanceof Error ? error.message : 'Failed to load billing data'
      }))
    }
  }

  const refresh = async () => {
    await fetchBillingData()
  }

  useEffect(() => {
    fetchBillingData()
  }, [])

  return {
    ...data,
    refresh
  }
}
