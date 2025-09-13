'use client'

import React, { useState, useEffect } from 'react'
import { useAuth } from '@/lib/auth-context'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Clock, AlertTriangle } from 'lucide-react'

export function InactivityWarning() {
  const { isAuthenticated, lastActivity, inactivityTimeout } = useAuth()
  const [showWarning, setShowWarning] = useState(false)
  const [timeRemaining, setTimeRemaining] = useState(0)

  useEffect(() => {
    if (!isAuthenticated) {
      setShowWarning(false)
      return
    }

    const checkInactivity = () => {
      const now = Date.now()
      const timeSinceActivity = now - lastActivity
      const timeLeft = inactivityTimeout - timeSinceActivity

      if (timeLeft <= 60000 && timeLeft > 0) { // Show warning in last minute
        setShowWarning(true)
        setTimeRemaining(Math.ceil(timeLeft / 1000))
      } else {
        setShowWarning(false)
      }
    }

    // Check every 10 seconds
    const interval = setInterval(checkInactivity, 10000)
    checkInactivity() // Check immediately

    return () => clearInterval(interval)
  }, [isAuthenticated, lastActivity, inactivityTimeout])

  if (!showWarning) return null

  return (
    <Alert className="fixed top-4 right-4 z-50 max-w-sm bg-orange-50 border-orange-200 dark:bg-orange-950 dark:border-orange-800">
      <AlertTriangle className="h-4 w-4 text-orange-600" />
      <AlertDescription className="text-orange-800 dark:text-orange-200">
        <div className="flex items-center gap-2">
          <Clock className="h-4 w-4" />
          <span className="font-medium">
            Auto-logout in {timeRemaining} seconds
          </span>
        </div>
        <p className="text-sm mt-1">
          Click anywhere to stay logged in
        </p>
      </AlertDescription>
    </Alert>
  )
}