'use client'

import React, { createContext, useContext, useEffect, useState } from 'react'

interface TenantInfo {
  slug: string
  name: string
  domain: string
  subscription: 'free'
  isCustomDomain: boolean
}

interface TenantContextValue {
  tenant: TenantInfo | null
  isLoading: boolean
  error: string | null
  refreshTenant: () => Promise<void>
}

const TenantContext = createContext<TenantContextValue | undefined>(undefined)

interface TenantProviderProps {
  children: React.ReactNode
  host: string
}

export function TenantProvider({ children, host }: TenantProviderProps) {
  const [tenant, setTenant] = useState<TenantInfo | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const detectTenant = async () => {
    try {
      setIsLoading(true)
      setError(null)

      // Parse subdomain from host
      const hostname = host.split(':')[0] // Remove port if present
      const parts = hostname.split('.')

      let tenantSlug: string | null = null
      let isCustomDomain = false

      // Check if it's a subdomain of our main domain
      if (parts.length > 2 && (hostname.includes('codeflowops.com') || hostname.includes('localhost'))) {
        tenantSlug = parts[0]
        if (tenantSlug === 'www' || tenantSlug === 'app') {
          tenantSlug = null // Main domain
        }
      } else if (parts.length >= 2 && !hostname.includes('localhost')) {
        // Custom domain
        isCustomDomain = true
        // Look up tenant by custom domain
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tenants/by-domain`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ domain: hostname }),
        })

        if (response.ok) {
          const data = await response.json()
          setTenant({
            slug: data.slug,
            name: data.name,
            domain: hostname,
            subscription: 'free',
            isCustomDomain: true,
          })
          setIsLoading(false)
          return
        }
      }

      if (tenantSlug) {
        // Fetch tenant info from API
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/tenants/${tenantSlug}`)
        
        if (response.ok) {
          const data = await response.json()
          setTenant({
            slug: data.slug,
            name: data.name,
            domain: data.custom_domain || `${data.slug}.codeflowops.com`,
            subscription: 'free',
            isCustomDomain,
          })
        } else if (response.status === 404) {
          setError('Tenant not found')
        } else {
          throw new Error('Failed to fetch tenant info')
        }
      } else {
        // Main domain - no specific tenant
        setTenant(null)
      }
    } catch (err) {
      console.error('Error detecting tenant:', err)
      setError('Failed to load tenant information')
    } finally {
      setIsLoading(false)
    }
  }

  const refreshTenant = async () => {
    await detectTenant()
  }

  useEffect(() => {
    detectTenant()
  }, [host])

  const value: TenantContextValue = {
    tenant,
    isLoading,
    error,
    refreshTenant,
  }

  return (
    <TenantContext.Provider value={value}>
      {children}
    </TenantContext.Provider>
  )
}

export function useTenant() {
  const context = useContext(TenantContext)
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider')
  }
  return context
}

// Utility hooks
export function useIsTenantSubdomain() {
  const { tenant } = useTenant()
  return !!tenant && !tenant.isCustomDomain
}

export function useIsCustomDomain() {
  const { tenant } = useTenant()
  return !!tenant && tenant.isCustomDomain
}

export function useIsMainDomain() {
  const { tenant } = useTenant()
  return !tenant
}
