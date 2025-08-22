'use client'

import { useEffect, useState } from 'react'

interface NoSSRIconProps {
  children: React.ReactNode
  fallback?: React.ReactNode
}

export function NoSSRIcon({ children, fallback = null }: NoSSRIconProps) {
  const [hasMounted, setHasMounted] = useState(false)

  useEffect(() => {
    setHasMounted(true)
  }, [])

  if (!hasMounted) {
    return <>{fallback}</>
  }

  return <>{children}</>
}

export default NoSSRIcon
