'use client'

import { usePathname } from 'next/navigation'
import Link from 'next/link'
import { ChevronRight, Home } from 'lucide-react'
import { cn } from '@/lib/utils'

interface BreadcrumbItem {
  label: string
  href?: string
  current?: boolean
}

const routeLabels: Record<string, string> = {
  dashboard: 'Dashboard',
  deployments: 'Deployments',
  templates: 'Templates',
  analytics: 'Analytics',
  monitoring: 'Monitoring',
  team: 'Team',
  // billing: 'Billing', // Removed (Stripe functionality removed)
  settings: 'Settings',
  support: 'Support',
  profile: 'Profile',
  create: 'Create',
  edit: 'Edit',
  active: 'Active',
  history: 'History'
}

export function BreadcrumbNavigation() {
  const pathname = usePathname()
  
  const generateBreadcrumbs = (): BreadcrumbItem[] => {
    // Remove leading slash and split by /
    const pathSegments = pathname.split('/').filter(Boolean)
    
    // Always start with Dashboard for authenticated routes
    const breadcrumbs: BreadcrumbItem[] = [
      {
        label: 'Dashboard',
        href: '/dashboard'
      }
    ]
    
    // Skip the first 'dashboard' segment since we already have it
    const relevantSegments = pathSegments.slice(1)
    
    // Build cumulative path for each segment
    let currentPath = '/dashboard'
    
    relevantSegments.forEach((segment, index) => {
      currentPath += `/${segment}`
      const isLast = index === relevantSegments.length - 1
      
      // Check if this is a dynamic route (UUID-like)
      const isId = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(segment)
      
      breadcrumbs.push({
        label: isId ? 'Details' : (routeLabels[segment] || segment.charAt(0).toUpperCase() + segment.slice(1)),
        href: isLast ? undefined : currentPath,
        current: isLast
      })
    })
    
    return breadcrumbs
  }

  const breadcrumbs = generateBreadcrumbs()
  
  // Don't show breadcrumbs on the main dashboard
  if (pathname === '/dashboard') {
    return null
  }

  return (
    <nav className="flex items-center space-x-1 text-sm text-gray-600">
      <ol className="flex items-center space-x-1">
        {breadcrumbs.map((crumb, index) => (
          <li key={crumb.href || index} className="flex items-center">
            {index > 0 && (
              <ChevronRight className="h-4 w-4 mx-2 text-gray-400" />
            )}
            
            {crumb.current ? (
              <span className="font-medium text-gray-900">
                {crumb.label}
              </span>
            ) : crumb.href ? (
              <Link
                href={crumb.href}
                className="text-gray-600 hover:text-gray-900 transition-colors"
              >
                {index === 0 && (
                  <Home className="h-4 w-4 mr-1 inline" />
                )}
                {crumb.label}
              </Link>
            ) : (
              <span className="text-gray-600">
                {crumb.label}
              </span>
            )}
          </li>
        ))}
      </ol>
    </nav>
  )
}
