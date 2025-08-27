'use client'

import { useAuth } from '@/lib/auth-context'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { User, CheckCircle, AlertTriangle, RefreshCw, LogOut } from 'lucide-react'
import { GitHubLogin } from './github-login'

interface ProfileDebugProps {
  showActions?: boolean
  className?: string
}

export function ProfileDebug({ showActions = true, className }: ProfileDebugProps) {
  const { user, loading, isAuthenticated, fetchUserProfile, logout } = useAuth()

  if (loading) {
    return (
      <Card className={className}>
        <CardContent className="flex items-center justify-center p-6">
          <RefreshCw className="h-5 w-5 animate-spin mr-2" />
          Checking authentication...
        </CardContent>
      </Card>
    )
  }

  if (!isAuthenticated || !user) {
    return (
      <div className={className}>
        <Alert className="mb-4">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            You need to sign in to access subscription features and trial management.
          </AlertDescription>
        </Alert>
        
        {showActions && <GitHubLogin />}
      </div>
    )
  }

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <User className="h-5 w-5" />
          Authentication Status
          <Badge variant="secondary" className="ml-auto">
            <CheckCircle className="h-3 w-3 mr-1" />
            Authenticated
          </Badge>
        </CardTitle>
        <CardDescription>
          You are currently signed in and can access all features.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="font-medium">Username:</span>
            <div className="text-muted-foreground">{user.username || user.name || 'N/A'}</div>
          </div>
          <div>
            <span className="font-medium">Email:</span>
            <div className="text-muted-foreground">{user.email || 'N/A'}</div>
          </div>
          <div>
            <span className="font-medium">Provider:</span>
            <div className="text-muted-foreground capitalize">{user.provider || 'Unknown'}</div>
          </div>
          <div>
            <span className="font-medium">User ID:</span>
            <div className="text-muted-foreground font-mono text-xs">{user.id}</div>
          </div>
        </div>

        {showActions && (
          <div className="flex gap-2 pt-4 border-t">
            <Button
              variant="outline"
              onClick={fetchUserProfile}
              size="sm"
            >
              <RefreshCw className="h-3 w-3 mr-1" />
              Refresh Profile
            </Button>
            <Button
              variant="outline"
              onClick={logout}
              size="sm"
            >
              <LogOut className="h-3 w-3 mr-1" />
              Sign Out
            </Button>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
