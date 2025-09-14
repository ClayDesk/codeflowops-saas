'use client'

import { usePathname } from 'next/navigation'
import { Navbar } from '@/components/landing/Navbar'

export function ConditionalNavbar() {
  const pathname = usePathname()

  // Hide navbar on checkout and auth pages for cleaner UX
  const hideNavbar = pathname?.includes('/checkout') ||
                    pathname?.includes('/login') ||
                    pathname?.includes('/register') ||
                    pathname?.includes('/reset-password')

  if (hideNavbar) {
    return null
  }

  return <Navbar />
}