'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip'
import {
  LayoutDashboard,
  Rocket,
  FileText,
  BarChart3,
  CreditCard,
  Settings,
  HelpCircle,
  ChevronLeft,
  ChevronRight,
  Zap,
  Activity,
  Cloud,
  GitBranch,
  Users,
  Bell
} from 'lucide-react'

interface NavigationItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
  description?: string
  children?: NavigationItem[]
}

const navigation: NavigationItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard,
    description: 'Overview and quick actions'
  },
  {
    name: 'Deployments',
    href: '/dashboard/deployments',
    icon: Rocket,
    description: 'Manage your deployments',
    children: [
      { name: 'Active', href: '/dashboard/deployments/active', icon: Activity },
      { name: 'History', href: '/dashboard/deployments/history', icon: GitBranch },
      { name: 'Create New', href: '/dashboard/deployments/create', icon: Zap }
    ]
  },
  {
    name: 'Templates',
    href: '/dashboard/templates',
    icon: FileText,
    description: 'Browse and manage templates'
  },
  {
    name: 'Analytics',
    href: '/dashboard/analytics',
    icon: BarChart3,
    description: 'Usage metrics and insights'
  },
  {
    name: 'Monitoring',
    href: '/dashboard/monitoring',
    icon: Activity,
    description: 'Real-time system monitoring'
  },
  {
    name: 'Team',
    href: '/dashboard/team',
    icon: Users,
    description: 'Manage team members'
  }
]

const bottomNavigation: NavigationItem[] = [
  {
    name: 'Billing',
    href: '/dashboard/billing',
    icon: CreditCard,
    description: 'Manage subscription and billing'
  },
  {
    name: 'Settings',
    href: '/dashboard/settings',
    icon: Settings,
    description: 'Account and preferences'
  },
  {
    name: 'Support',
    href: '/dashboard/support',
    icon: HelpCircle,
    description: 'Get help and documentation'
  }
]

interface SidebarNavigationProps {
  collapsed?: boolean
  onToggleCollapse?: () => void
}

export function SidebarNavigation({ collapsed = false, onToggleCollapse }: SidebarNavigationProps) {
  const pathname = usePathname()
  const [expandedItems, setExpandedItems] = useState<string[]>([])

  const toggleExpanded = (itemName: string) => {
    if (collapsed) return // Don't allow expansion when collapsed
    
    setExpandedItems(prev => 
      prev.includes(itemName) 
        ? prev.filter(name => name !== itemName)
        : [...prev, itemName]
    )
  }

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  const NavItem = ({ item, isChild = false }: { item: NavigationItem; isChild?: boolean }) => {
    const active = isActive(item.href)
    const hasChildren = item.children && item.children.length > 0
    const isExpanded = expandedItems.includes(item.name)
    const Icon = item.icon

    const content = (
      <div className="flex items-center justify-between w-full">
        <div className="flex items-center gap-3">
          <Icon className={cn(
            "h-5 w-5 transition-colors",
            active ? "text-blue-600" : "text-gray-500"
          )} />
          {!collapsed && (
            <span className={cn(
              "font-medium transition-colors",
              active ? "text-blue-600" : "text-gray-700",
              isChild && "text-sm"
            )}>
              {item.name}
            </span>
          )}
        </div>
        
        {!collapsed && (
          <div className="flex items-center gap-2">
            {item.badge && (
              <Badge variant="secondary" className="h-5 text-xs">
                {item.badge}
              </Badge>
            )}
            {hasChildren && !collapsed && (
              <ChevronRight className={cn(
                "h-4 w-4 transition-transform text-gray-400",
                isExpanded && "rotate-90"
              )} />
            )}
          </div>
        )}
      </div>
    )

    if (hasChildren && !collapsed) {
      return (
        <div className={cn("space-y-1", isChild && "ml-6")}>
          <Button
            variant="ghost"
            className={cn(
              "w-full justify-start h-10 px-3",
              active && "bg-blue-50 text-blue-600 hover:bg-blue-100"
            )}
            onClick={() => toggleExpanded(item.name)}
          >
            {content}
          </Button>
          
          {isExpanded && (
            <div className="space-y-1 ml-6">
              {item.children!.map((child) => (
                <NavItem key={child.href} item={child} isChild />
              ))}
            </div>
          )}
        </div>
      )
    }

    const button = (
      <Button
        variant="ghost"
        className={cn(
          "w-full justify-start h-10 px-3",
          active && "bg-blue-50 text-blue-600 hover:bg-blue-100",
          isChild && "ml-6 text-sm"
        )}
        asChild
      >
        <Link href={item.href}>
          {content}
        </Link>
      </Button>
    )

    if (collapsed && item.description) {
      return (
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              {button}
            </TooltipTrigger>
            <TooltipContent side="right" className="ml-2">
              <div className="font-medium">{item.name}</div>
              <div className="text-sm text-muted-foreground">{item.description}</div>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      )
    }

    return button
  }

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className={cn(
        "flex items-center gap-3 p-4 border-b border-gray-200",
        collapsed ? "justify-center" : "justify-between"
      )}>
        {!collapsed && (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-gradient-to-br from-blue-600 to-blue-700 rounded-lg flex items-center justify-center">
              <Cloud className="h-5 w-5 text-white" />
            </div>
            <div>
              <div className="font-bold text-gray-900">CodeFlowOps</div>
              <div className="text-xs text-gray-500">Smart Deploy</div>
            </div>
          </div>
        )}
        
        {onToggleCollapse && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onToggleCollapse}
            className="h-8 w-8 p-0"
          >
            {collapsed ? (
              <ChevronRight className="h-4 w-4" />
            ) : (
              <ChevronLeft className="h-4 w-4" />
            )}
          </Button>
        )}
      </div>

      {/* Main Navigation */}
      <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
        {navigation.map((item) => (
          <NavItem key={item.href} item={item} />
        ))}
      </nav>

      {/* Bottom Navigation */}
      <div className="border-t border-gray-200 p-3 space-y-1">
        {bottomNavigation.map((item) => (
          <NavItem key={item.href} item={item} />
        ))}
      </div>

      {/* Status Indicator (when not collapsed) */}
      {!collapsed && (
        <div className="p-3 border-t border-gray-200">
          <div className="flex items-center gap-2 text-sm text-gray-600">
            <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
            <span>All systems operational</span>
          </div>
        </div>
      )}
    </div>
  )
}
