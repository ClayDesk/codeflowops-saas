'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { 
  Menu, 
  X, 
  Zap, 
  ChevronDown,
  Github,
  Twitter,
  Linkedin
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navigation = [
  { name: 'Dashboard', href: '/dashboard' },
  { name: 'Features', href: '#features' },
  { name: 'Docs', href: '/docs' },
  { name: 'Blog', href: '/blog' },
]

const solutions = [
  {
    name: 'CI/CD Automation',
    description: 'Streamline your development pipeline',
    href: '/solutions/cicd',
  },
  {
    name: 'Multi-Tenant Deployments',
    description: 'Scale across multiple environments',
    href: '/solutions/multi-tenant',
  },
  {
    name: 'Infrastructure as Code',
    description: 'Terraform automation at scale',
    href: '/solutions/iac',
  },
  {
    name: 'Enterprise Integration',
    description: 'GitHub, AWS, and more',
    href: '/solutions/integrations',
  },
]

export function LandingHeader() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false)

  return (
    <header className="sticky top-0 z-50 w-full border-b border-border/40 bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <nav className="mx-auto flex max-w-7xl items-center justify-between p-6 lg:px-8" aria-label="Global">
        <div className="flex lg:flex-1">
          <Link href="/" className="-m-1.5 p-1.5 flex items-center space-x-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
              <Zap className="h-5 w-5 text-primary-foreground" />
            </div>
            <span className="text-xl font-bold">CodeFlowOps</span>
          </Link>
        </div>
        
        <div className="flex lg:hidden">
          <button
            type="button"
            className="-m-2.5 inline-flex items-center justify-center rounded-md p-2.5 text-foreground"
            onClick={() => setMobileMenuOpen(true)}
          >
            <span className="sr-only">Open main menu</span>
            <Menu className="h-6 w-6" aria-hidden="true" />
          </button>
        </div>
        
        <div className="hidden lg:flex lg:gap-x-12">
          {/* Solutions Dropdown */}
          <div className="relative group">
            <button className="flex items-center gap-x-1 text-sm font-semibold leading-6 text-foreground hover:text-primary transition-colors">
              Solutions
              <ChevronDown className="h-4 w-4 transition-transform group-hover:rotate-180" aria-hidden="true" />
            </button>
            
            <div className="absolute left-1/2 top-full z-10 mt-3 w-screen max-w-md -translate-x-1/2 transform px-2 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200">
              <div className="rounded-lg bg-background shadow-lg ring-1 ring-border overflow-hidden">
                <div className="p-4">
                  {solutions.map((item) => (
                    <Link
                      key={item.name}
                      href={item.href}
                      className="group relative flex items-center gap-x-6 rounded-lg p-4 text-sm leading-6 hover:bg-muted transition-colors"
                    >
                      <div className="flex-auto">
                        <div className="block font-semibold text-foreground">
                          {item.name}
                          <span className="absolute inset-0" />
                        </div>
                        <p className="mt-1 text-muted-foreground">{item.description}</p>
                      </div>
                    </Link>
                  ))}
                </div>
              </div>
            </div>
          </div>
          
          {navigation.map((item) => (
            <Link
              key={item.name}
              href={item.href}
              className="text-sm font-semibold leading-6 text-foreground hover:text-primary transition-colors"
            >
              {item.name}
            </Link>
          ))}
        </div>
        
        <div className="hidden lg:flex lg:flex-1 lg:justify-end lg:gap-x-4">
          <Link href="/auth/login">
            <Button variant="ghost" size="sm">
              Sign in
            </Button>
          </Link>
          <Link href="/auth/signup">
            <Button size="sm">
              Start free trial
            </Button>
          </Link>
        </div>
      </nav>
      
      {/* Mobile menu */}
      <div className={cn(
        "fixed inset-0 z-50 lg:hidden",
        mobileMenuOpen ? "block" : "hidden"
      )}>
        <div className="fixed inset-0 bg-background/80 backdrop-blur" onClick={() => setMobileMenuOpen(false)} />
        <div className="fixed inset-y-0 right-0 z-50 w-full overflow-y-auto bg-background px-6 py-6 sm:max-w-sm sm:ring-1 sm:ring-border">
          <div className="flex items-center justify-between">
            <Link href="/" className="-m-1.5 p-1.5 flex items-center space-x-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-md bg-primary">
                <Zap className="h-5 w-5 text-primary-foreground" />
              </div>
              <span className="text-xl font-bold">CodeFlowOps</span>
            </Link>
            <button
              type="button"
              className="-m-2.5 rounded-md p-2.5 text-foreground"
              onClick={() => setMobileMenuOpen(false)}
            >
              <span className="sr-only">Close menu</span>
              <X className="h-6 w-6" aria-hidden="true" />
            </button>
          </div>
          
          <div className="mt-6 flow-root">
            <div className="-my-6 divide-y divide-border">
              <div className="space-y-2 py-6">
                <div className="-mx-3">
                  <div className="mx-3 block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground">
                    Solutions
                  </div>
                  {solutions.map((item) => (
                    <Link
                      key={item.name}
                      href={item.href}
                      className="mx-3 block rounded-lg px-3 py-2 text-base leading-7 text-muted-foreground hover:bg-muted"
                      onClick={() => setMobileMenuOpen(false)}
                    >
                      {item.name}
                    </Link>
                  ))}
                </div>
                
                {navigation.map((item) => (
                  <Link
                    key={item.name}
                    href={item.href}
                    className="-mx-3 block rounded-lg px-3 py-2 text-base font-semibold leading-7 text-foreground hover:bg-muted"
                    onClick={() => setMobileMenuOpen(false)}
                  >
                    {item.name}
                  </Link>
                ))}
              </div>
              
              <div className="py-6 space-y-4">
                <Link href="/auth/login" onClick={() => setMobileMenuOpen(false)}>
                  <Button variant="ghost" className="w-full">
                    Sign in
                  </Button>
                </Link>
                <Link href="/auth/signup" onClick={() => setMobileMenuOpen(false)}>
                  <Button className="w-full">
                    Start free trial
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      </div>
    </header>
  )
}
