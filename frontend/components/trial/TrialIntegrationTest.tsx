"use client"

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../ui/card"
import { Button } from "../ui/button"
import { Badge } from "../ui/badge"
import { Clock, TrendingUp, AlertTriangle, CheckCircle, XCircle, Loader2 } from 'lucide-react'
import { useTrialData } from "../../hooks/use-trial-data"

export function TrialIntegrationTest() {
  const { trial, loading, error, refetch } = useTrialData()

  if (loading) {
    return (
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span>Loading trial data...</span>
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error) {
    return (
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-red-600">
            <XCircle className="h-5 w-5" />
            Connection Error
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-red-600 mb-3">{error}</p>
          <Button onClick={refetch} variant="outline">
            <span>Retry Connection</span>
          </Button>
        </CardContent>
      </Card>
    )
  }

  if (!trial) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>⚠️ No Trial Data</CardTitle>
        </CardHeader>
        <CardContent>
          <p>No trial data available</p>
          <Button onClick={refetch} variant="outline" className="mt-2">
            Refresh
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          ✅ Trial Integration Working
          <Badge variant="secondary">Connected</Badge>
        </CardTitle>
        <CardDescription>
          Live data from backend trial management system
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Trial Metrics Summary */}
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-1">
              <Clock className="h-4 w-4 text-blue-500" />
              <span className="text-sm font-medium">Days Remaining</span>
            </div>
            <div className="text-2xl font-bold text-blue-600">
              {trial.metrics?.days_remaining || 0}
            </div>
          </div>
          
          <div className="space-y-1">
            <div className="flex items-center gap-1">
              <TrendingUp className="h-4 w-4 text-green-500" />
              <span className="text-sm font-medium">Usage</span>
            </div>
            <div className="text-2xl font-bold text-green-600">
              {trial.metrics?.usage_percentage?.toFixed(0) || 0}%
            </div>
          </div>
        </div>

        {/* Engagement Metrics */}
        <div className="bg-gray-50 p-3 rounded-lg">
          <h4 className="font-medium text-sm mb-2">Trial Analytics</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            <div>
              <span className="text-gray-600">Engagement:</span>
              <span className="ml-1 font-medium">
                {trial.metrics?.engagement_score 
                  ? `${(trial.metrics.engagement_score * 100).toFixed(0)}%`
                  : 'N/A'
                }
              </span>
            </div>
            <div>
              <span className="text-gray-600">Conversion:</span>
              <span className="ml-1 font-medium">
                {trial.metrics?.conversion_likelihood 
                  ? `${(trial.metrics.conversion_likelihood * 100).toFixed(0)}%`
                  : 'N/A'
                }
              </span>
            </div>
          </div>
        </div>

        {/* Warnings */}
        {trial.warnings && (
          <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg">
            <div className="flex items-center gap-2">
              <AlertTriangle className="h-4 w-4 text-yellow-600" />
              <span className="font-medium text-yellow-800">{trial.warnings.title}</span>
            </div>
            <p className="text-sm text-yellow-700 mt-1">{trial.warnings.message}</p>
          </div>
        )}

        {/* Recommendations Count */}
        {trial.recommendations && trial.recommendations.length > 0 && (
          <div className="bg-blue-50 border border-blue-200 p-3 rounded-lg">
            <p className="text-sm text-blue-700">
              📋 {trial.recommendations.length} personalized recommendations available
            </p>
            <div className="mt-2 space-y-1">
              {trial.recommendations.slice(0, 2).map((rec, index) => (
                <div key={index} className="text-xs text-blue-600">
                  • {rec.title}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Raw Data Toggle */}
        <details className="text-xs">
          <summary className="cursor-pointer text-gray-600 hover:text-gray-800">
            🔍 View Raw Trial Data
          </summary>
          <pre className="mt-2 bg-gray-100 p-2 rounded text-xs overflow-auto max-h-40">
            {JSON.stringify(trial, null, 2)}
          </pre>
        </details>

        {/* Refresh Button */}
        <Button onClick={refetch} variant="outline" size="sm" className="w-full">
          <CheckCircle className="h-4 w-4 mr-2" />
          Refresh Data
        </Button>
      </CardContent>
    </Card>
  )
}
