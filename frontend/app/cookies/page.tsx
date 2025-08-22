'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Switch } from '@/components/ui/switch'
import { Cookie, Settings, Shield, Calendar, FileText, AlertTriangle, CheckCircle, Eye, Target, BarChart3 } from 'lucide-react'

export default function CookiePolicyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Cookie className="h-12 w-12 text-amber-600 mr-3" />
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100">
              Cookie Policy
            </h1>
          </div>
          <p className="text-xl text-slate-600 dark:text-slate-400 mb-4">
            CodeFlowOps Platform (by ClayDesk LLC)
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm text-slate-500">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-1" />
              Effective: August 21, 2025
            </div>
            <div className="flex items-center">
              <FileText className="h-4 w-4 mr-1" />
              Last Updated: August 21, 2025
            </div>
          </div>
        </div>

        {/* Introduction */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Cookie className="h-5 w-5 mr-2" />
              What Are Cookies?
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              Cookies are small text files that are placed on your device when you visit our website. 
              They help us provide you with a better experience by remembering your preferences and 
              analyzing how you use our service.
            </p>
            <p>
              This Cookie Policy explains what cookies we use, why we use them, and how you can 
              manage your cookie preferences for the CodeFlowOps platform.
            </p>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                <Shield className="h-4 w-4 inline mr-1" />
                <strong>Your Control:</strong> You can manage your cookie preferences at any time through 
                your browser settings or our cookie preference center.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Cookie Categories */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Types of Cookies We Use</CardTitle>
            <CardDescription>
              We categorize cookies based on their purpose and functionality
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Strictly Necessary */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Shield className="h-5 w-5 text-red-600" />
                  <h4 className="font-semibold text-lg">Strictly Necessary Cookies</h4>
                  <Badge variant="destructive">Always Active</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                These cookies are essential for the website to function properly. They enable core functionality 
                such as security, network management, and accessibility.
              </p>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Authentication Tokens</span>
                  <Badge variant="outline">Session</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Security & CSRF Protection</span>
                  <Badge variant="outline">Session</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Load Balancing</span>
                  <Badge variant="outline">Session</Badge>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Cannot be disabled as they are necessary for the platform to function.
              </p>
            </div>

            {/* Functional */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Settings className="h-5 w-5 text-blue-600" />
                  <h4 className="font-semibold text-lg">Functional Cookies</h4>
                  <Switch defaultChecked />
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                These cookies enable enhanced functionality and personalization, such as remembering 
                your preferences and providing personalized content.
              </p>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Theme Preferences (Dark/Light)</span>
                  <Badge variant="outline">30 days</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Language Settings</span>
                  <Badge variant="outline">30 days</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Dashboard Layout Preferences</span>
                  <Badge variant="outline">90 days</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Collapsed/Expanded Sidebar</span>
                  <Badge variant="outline">30 days</Badge>
                </div>
              </div>
            </div>

            {/* Analytics */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <BarChart3 className="h-5 w-5 text-green-600" />
                  <h4 className="font-semibold text-lg">Analytics Cookies</h4>
                  <Switch defaultChecked />
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                These cookies help us understand how visitors interact with our platform by providing 
                information about areas visited, time spent, and any issues encountered.
              </p>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Google Analytics</span>
                  <Badge variant="outline">2 years</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Usage Patterns</span>
                  <Badge variant="outline">1 year</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Performance Metrics</span>
                  <Badge variant="outline">90 days</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Error Tracking</span>
                  <Badge variant="outline">30 days</Badge>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Data is anonymized and used for improving service quality.
              </p>
            </div>

            {/* Marketing */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Target className="h-5 w-5 text-purple-600" />
                  <h4 className="font-semibold text-lg">Marketing Cookies</h4>
                  <Switch />
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                These cookies are used to deliver personalized advertisements and measure the effectiveness 
                of advertising campaigns.
              </p>
              <div className="space-y-2">
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Advertising Preferences</span>
                  <Badge variant="outline">1 year</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Campaign Tracking</span>
                  <Badge variant="outline">90 days</Badge>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="font-medium">Social Media Integration</span>
                  <Badge variant="outline">6 months</Badge>
                </div>
              </div>
              <p className="text-xs text-slate-500 mt-2">
                Disabled by default. Requires explicit consent.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Detailed Cookie Table */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Detailed Cookie Information</CardTitle>
            <CardDescription>
              Complete list of cookies used by CodeFlowOps platform
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b">
                    <th className="text-left p-2 font-semibold">Cookie Name</th>
                    <th className="text-left p-2 font-semibold">Category</th>
                    <th className="text-left p-2 font-semibold">Purpose</th>
                    <th className="text-left p-2 font-semibold">Duration</th>
                    <th className="text-left p-2 font-semibold">Domain</th>
                  </tr>
                </thead>
                <tbody className="text-xs">
                  <tr className="border-b">
                    <td className="p-2 font-mono">cfo_session</td>
                    <td className="p-2"><Badge variant="destructive" className="text-xs">Necessary</Badge></td>
                    <td className="p-2">User authentication and session management</td>
                    <td className="p-2">Session</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-mono">cfo_csrf</td>
                    <td className="p-2"><Badge variant="destructive" className="text-xs">Necessary</Badge></td>
                    <td className="p-2">Cross-Site Request Forgery protection</td>
                    <td className="p-2">Session</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-mono">cfo_theme</td>
                    <td className="p-2"><Badge variant="secondary" className="text-xs">Functional</Badge></td>
                    <td className="p-2">Remember dark/light theme preference</td>
                    <td className="p-2">30 days</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-mono">cfo_sidebar</td>
                    <td className="p-2"><Badge variant="secondary" className="text-xs">Functional</Badge></td>
                    <td className="p-2">Remember sidebar collapsed/expanded state</td>
                    <td className="p-2">30 days</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-mono">_ga</td>
                    <td className="p-2"><Badge variant="outline" className="text-xs">Analytics</Badge></td>
                    <td className="p-2">Google Analytics - distinguish users</td>
                    <td className="p-2">2 years</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-mono">_ga_XXXXXXXXXX</td>
                    <td className="p-2"><Badge variant="outline" className="text-xs">Analytics</Badge></td>
                    <td className="p-2">Google Analytics - session state</td>
                    <td className="p-2">2 years</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-mono">cfo_analytics</td>
                    <td className="p-2"><Badge variant="outline" className="text-xs">Analytics</Badge></td>
                    <td className="p-2">Internal usage analytics and performance tracking</td>
                    <td className="p-2">1 year</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                  <tr className="border-b">
                    <td className="p-2 font-mono">cfo_marketing</td>
                    <td className="p-2"><Badge className="text-xs bg-purple-100 text-purple-800">Marketing</Badge></td>
                    <td className="p-2">Track marketing campaign effectiveness</td>
                    <td className="p-2">90 days</td>
                    <td className="p-2">codeflowops.com</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        {/* Third-Party Cookies */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Eye className="h-5 w-5 mr-2" />
              Third-Party Cookies
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              Some cookies on our platform are set by third-party services that appear on our pages. 
              We do not control these cookies, and you should check the third-party websites for more information.
            </p>
            
            <div className="space-y-4">
              <div className="border-l-4 border-blue-500 pl-4">
                <h4 className="font-semibold">Google Analytics</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Provides website analytics to help us understand user behavior and improve our service.
                </p>
                <p className="text-xs text-slate-500">
                  Privacy Policy: <a href="https://policies.google.com/privacy" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">Google Privacy Policy</a>
                </p>
              </div>
              
              <div className="border-l-4 border-green-500 pl-4">
                <h4 className="font-semibold">AWS CloudFront</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Content delivery network cookies for optimizing performance and security.
                </p>
                <p className="text-xs text-slate-500">
                  Privacy Policy: <a href="https://aws.amazon.com/privacy/" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">AWS Privacy Notice</a>
                </p>
              </div>
              
              <div className="border-l-4 border-purple-500 pl-4">
                <h4 className="font-semibold">GitHub OAuth</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Authentication cookies when you sign in with GitHub.
                </p>
                <p className="text-xs text-slate-500">
                  Privacy Policy: <a href="https://docs.github.com/en/site-policy/privacy-policies/github-privacy-statement" className="text-blue-600 hover:underline" target="_blank" rel="noopener noreferrer">GitHub Privacy Statement</a>
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Cookie Management */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Managing Your Cookie Preferences
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h4 className="font-semibold mb-2">Cookie Preference Center</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                You can manage your cookie preferences at any time by clicking the cookie settings button 
                in our website footer or using the button below.
              </p>
              <Button variant="outline" className="mb-4">
                <Settings className="h-4 w-4 mr-2" />
                Manage Cookie Preferences
              </Button>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Browser Settings</h4>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                You can also control cookies through your browser settings. Most browsers allow you to:
              </p>
              <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 dark:text-slate-400 ml-4">
                <li>View and delete cookies</li>
                <li>Block cookies from specific sites</li>
                <li>Block third-party cookies</li>
                <li>Block all cookies</li>
                <li>Delete all cookies when you close the browser</li>
              </ul>
            </div>
            
            <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg">
              <div className="flex items-start space-x-2">
                <AlertTriangle className="h-5 w-5 text-amber-600 flex-shrink-0 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-amber-800 dark:text-amber-200">Important Note</h4>
                  <p className="text-amber-700 dark:text-amber-300 text-sm">
                    Disabling certain cookies may impact the functionality of our platform. 
                    Strictly necessary cookies cannot be disabled as they are essential for the service to work.
                  </p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Global Privacy Control */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              Global Privacy Control (GPC)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              We respect the Global Privacy Control (GPC) signal. When we detect a GPC signal from your browser, 
              we will honor your preference and:
            </p>
            <ul className="list-disc list-inside space-y-1 text-sm text-slate-600 dark:text-slate-400 ml-4">
              <li>Disable non-essential cookies automatically</li>
              <li>Opt you out of data sharing with third parties</li>
              <li>Apply privacy-friendly defaults to your account</li>
            </ul>
            <div className="flex items-center space-x-2 text-sm">
              <CheckCircle className="h-4 w-4 text-green-600" />
              <span>GPC Signal Detected: <span className="font-mono">false</span></span>
            </div>
          </CardContent>
        </Card>

        {/* Data Retention */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Cookie Data Retention</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2">Session Cookies</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Deleted automatically when you close your browser or log out.
                </p>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Persistent Cookies</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Stored for specific periods as indicated in the cookie table above.
                </p>
              </div>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              We regularly review and delete expired cookies. You can also manually clear cookies 
              at any time through your browser settings or our cookie preference center.
            </p>
          </CardContent>
        </Card>

        {/* Legal Basis */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Legal Basis for Cookie Processing</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <Badge className="mb-2">Necessary Cookies</Badge>
                <p className="text-sm">Processed under legitimate interest for website functionality</p>
              </div>
              <div>
                <Badge className="mb-2">Functional Cookies</Badge>
                <p className="text-sm">Processed based on your consent and legitimate interest</p>
              </div>
              <div>
                <Badge className="mb-2">Analytics Cookies</Badge>
                <p className="text-sm">Processed based on your consent</p>
              </div>
              <div>
                <Badge className="mb-2">Marketing Cookies</Badge>
                <p className="text-sm">Processed only with your explicit consent</p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Changes to Cookie Policy */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Changes to This Cookie Policy</CardTitle>
          </CardHeader>
          <CardContent>
            <p>
              We may update this Cookie Policy from time to time to reflect changes in our practices 
              or for other operational, legal, or regulatory reasons. We will notify you of any 
              material changes by posting the updated policy on our website and updating the 
              "Last Updated" date.
            </p>
          </CardContent>
        </Card>

        {/* Contact Information */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Contact Us About Cookies</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              If you have any questions about our use of cookies or this Cookie Policy, please contact us:
            </p>
            <div className="space-y-2">
              <div>
                <strong>Email:</strong> privacy@claydesk.com
              </div>
              <div>
                <strong>Address:</strong>
                <br />
                ClayDesk LLC
                <br />
                45 Burgundy Hills Lane
                <br />
                Middletown, CT 06457, USA
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            This cookie policy is effective as of August 21, 2025. 
            For questions about this policy, contact privacy@claydesk.com
          </p>
          <p className="mt-2">
            Related documents: <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a> • 
            <a href="/terms" className="text-blue-600 hover:underline ml-1">Terms of Service</a>
          </p>
        </div>
      </div>
    </div>
  )
}
