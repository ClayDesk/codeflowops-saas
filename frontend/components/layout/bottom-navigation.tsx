'use client'

import { useState } from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { cn } from '@/lib/utils'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Sheet, SheetContent, SheetTrigger } from '@/components/ui/sheet'
import {
  LayoutDashboard,
  Rocket,
  Activity,
  MoreHorizontal,
  Menu,
  Bell,
  Settings,
  BarChart3,
  FileText,
  Users,
  CreditCard
} from 'lucide-react'

interface BottomNavItem {
  name: string
  href: string
  icon: React.ComponentType<{ className?: string }>
  badge?: string
}

const bottomNavItems: BottomNavItem[] = [
  {
    name: 'Dashboard',
    href: '/dashboard',
    icon: LayoutDashboard
  },
  {
    name: 'Deploy',
    href: '/dashboard/deployments/create',
    icon: Rocket
  },
  {
    name: 'Monitor',
    href: '/dashboard/monitoring',
    icon: Activity,
    badge: '3'
  },
  {
    name: 'More',
    href: '#',
    icon: MoreHorizontal
  }
]

const moreMenuItems = [
  { name: 'Templates', href: '/dashboard/templates', icon: FileText },
  { name: 'Analytics', href: '/dashboard/analytics', icon: BarChart3 },
  { name: 'Team', href: '/dashboard/team', icon: Users },
  { name: 'Billing', href: '/dashboard/billing', icon: CreditCard },
  { name: 'Settings', href: '/dashboard/settings', icon: Settings },
  { name: 'Notifications', href: '/dashboard/notifications', icon: Bell }
]

export function BottomNavigation() {
  const pathname = usePathname()
  const [moreMenuOpen, setMoreMenuOpen] = useState(false)

  const isActive = (href: string) => {
    if (href === '/dashboard') {
      return pathname === '/dashboard'
    }
    return pathname.startsWith(href)
  }

  const isMoreItemActive = () => {
    return moreMenuItems.some(item => isActive(item.href))
  }

  return (
    <>
      {/* Bottom Navigation Bar */}
      <nav className="lg:hidden fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 safe-area-pb z-50">
        <div className="flex items-center justify-around px-2 py-2">
          {bottomNavItems.map((item) => {
            const Icon = item.icon
            const active = item.name === 'More' ? isMoreItemActive() : isActive(item.href)
            
            if (item.name === 'More') {
              return (
                <Sheet key={item.name} open={moreMenuOpen} onOpenChange={setMoreMenuOpen}>
                  <SheetTrigger asChild>
                    <Button
                      variant="ghost"
                      className={cn(
                        "flex flex-col items-center gap-1 h-auto py-2 px-3 min-w-[64px]",
                        active && "text-blue-600"
                      )}
                    >
                      <div className="relative">
                        <Icon className="h-5 w-5" />
                      </div>
                      <span className="text-xs font-medium">{item.name}</span>
                    </Button>
                  </SheetTrigger>
                  <SheetContent side="bottom" className="h-[400px]">
                    <div className="py-4">
                      <h3 className="text-lg font-semibold mb-4">More Options</h3>
                      <div className="grid grid-cols-2 gap-2">
                        {moreMenuItems.map((menuItem) => {
                          const MenuIcon = menuItem.icon
                          const menuActive = isActive(menuItem.href)
                          
                          return (
                            <Button
                              key={menuItem.href}
                              variant="ghost"
                              className={cn(
                                "h-auto p-4 flex flex-col items-center gap-2",
                                menuActive && "bg-blue-50 text-blue-600"
                              )}
                              asChild
                              onClick={() => setMoreMenuOpen(false)}
                            >
                              <Link href={menuItem.href}>
                                <MenuIcon className="h-6 w-6" />
                                <span className="text-sm font-medium">{menuItem.name}</span>
                              </Link>
                            </Button>
                          )
                        })}
                      </div>
                    </div>
                  </SheetContent>
                </Sheet>
              )
            }

            return (
              <Button
                key={item.href}
                variant="ghost"
                className={cn(
                  "flex flex-col items-center gap-1 h-auto py-2 px-3 min-w-[64px]",
                  active && "text-blue-600"
                )}
                asChild
              >
                <Link href={item.href}>
                  <div className="relative">
                    <Icon className="h-5 w-5" />
                    {item.badge && (
                      <Badge 
                        variant="destructive" 
                        className="absolute -top-2 -right-2 h-4 w-4 flex items-center justify-center p-0 text-[10px]"
                      >
                        {item.badge}
                      </Badge>
                    )}
                  </div>
                  <span className="text-xs font-medium">{item.name}</span>
                </Link>
              </Button>
            )
          })}
        </div>
      </nav>

      {/* Bottom padding to prevent content from being hidden behind bottom nav */}
      <div className="lg:hidden h-16" />
    </>
  )
}
