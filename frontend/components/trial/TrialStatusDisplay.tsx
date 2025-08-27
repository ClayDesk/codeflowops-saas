"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { Badge } from "../ui/badge"
import { Button } from "../ui/button"
import { Progress } from "../ui/progress"
import { AlertTriangle, Clock, TrendingUp, CheckCircle } from 'lucide-react'
import { Alert, AlertDescription } from "../ui/alert"
import { useTrialData } from "../../hooks/use-trial-data"

export function TrialStatusDisplay() {
  const { trial, loading, error, refetch } = useTrialData()

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2">
            <div className="animate-spin rounded-full h-4 w-4 border-2 border-blue-600 border-t-transparent"></div>
            <span>Loading trial status...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Alert>
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>
          Failed to load trial status: {error}
          <Button onClick={refetch} variant="outline" size="sm" className="ml-2">
            Retry
          </Button>
        </AlertDescription>
      </Alert>
    )
  }

  if (!trial) {
    return (
      <Alert>
        <AlertDescription>
          No trial data available
        </AlertDescription>
      </Alert>
    )
  }

  const getHealthBadgeVariant = (health: string) => {
    switch (health) {
      case 'excellent':
        return 'default'
      case 'good':
        return 'secondary'
      case 'fair':
        return 'outline'
      case 'needs_attention':
        return 'destructive'
      default:
        return 'secondary'
    }
  }

  const getEngagementColor = (level: string) => {
    switch (level) {
      case 'highly_engaged':
        return 'text-green-600'
      case 'moderately_engaged':
        return 'text-yellow-600'
      case 'low_engagement':
        return 'text-red-600'
      default:
        return 'text-gray-600'
    }
  }

  return (
    <div className="space-y-4">
      {/* Main Trial Status Card */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Clock className="h-5 w-5" />
              Trial Status
            </CardTitle>
            <Badge variant="secondary">
              Trial Active
            </Badge>
          </div>
          <CardDescription>
            Your free trial progress and analytics
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          {/* Days Remaining */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Days Remaining</span>
              <span className="text-2xl font-bold text-blue-600">
                {trial.metrics?.days_remaining || 0}
              </span>
            </div>
          </div>

          {/* Usage Progress */}
          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Deployment Usage</span>
              <span className="text-sm text-gray-600">
                {trial.metrics?.deployments_used || 0} / {trial.metrics?.deployments_limit || 5}
              </span>
            </div>
            <Progress 
              value={trial.metrics?.usage_percentage || 0} 
              className="w-full"
            />
          </div>

          {/* Engagement Score */}
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-1">
                <TrendingUp className="h-4 w-4 text-green-500" />
                <span className="text-sm font-medium">Engagement</span>
              </div>
              <div className="text-lg font-bold text-green-600">
                {trial.metrics?.engagement_score 
                  ? `${(trial.metrics.engagement_score * 100).toFixed(0)}%`
                  : 'N/A'
                }
              </div>
            </div>
            
            <div className="space-y-1">
              <div className="flex items-center gap-1">
                <CheckCircle className="h-4 w-4 text-blue-500" />
                <span className="text-sm font-medium">Conversion</span>
              </div>
              <div className="text-lg font-bold text-blue-600">
                {trial.metrics?.conversion_likelihood 
                  ? `${(trial.metrics.conversion_likelihood * 100).toFixed(0)}%`
                  : 'N/A'
                }
              </div>
            </div>
          </div>

          {/* Warnings */}
          {trial.warnings && (
            <Alert>
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>
                <strong>{trial.warnings.title}</strong>
                <br />
                {trial.warnings.message}
              </AlertDescription>
            </Alert>
          )}

          {/* Recommendations */}
          {trial.recommendations && trial.recommendations.length > 0 && (
            <div className="space-y-2">
              <h4 className="text-sm font-medium">Recommendations</h4>
              <div className="space-y-1">
                {trial.recommendations.slice(0, 3).map((rec, index) => (
                  <div key={index} className="text-xs bg-blue-50 border border-blue-200 rounded px-2 py-1">
                    {rec.title}: {rec.description}
                  </div>
                ))}
                {trial.recommendations.length > 3 && (
                  <div className="text-xs text-gray-500">
                    +{trial.recommendations.length - 3} more recommendations
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Refresh Button */}
          <Button onClick={refetch} variant="outline" size="sm" className="w-full">
            Refresh Status
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
