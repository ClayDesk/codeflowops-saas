'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'
import { 
  Shield, 
  CheckCircle, 
  Calendar, 
  FileText, 
  Lock, 
  Globe, 
  Users, 
  Database, 
  CloudCog, 
  Settings, 
  AlertTriangle,
  Download,
  Eye,
  Building,
  Gavel,
  Mail,
  MapPin,
  Star,
  Target,
  Zap,
  Crown,
  CreditCard,
  Heart,
  Scale,
  Award,
  Verified,
  Flag,
  Key,
  Fingerprint,
  Server,
  Network,
  Bug,
  Timer,
  Cpu,
  HardDrive,
  Wifi,
  Monitor,
  ShieldCheck,
  UserCheck,
  Bell,
  Archive
} from 'lucide-react'

export default function SecurityPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <ShieldCheck className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100">
              Security & Infrastructure
            </h1>
          </div>
          <p className="text-xl text-slate-600 dark:text-slate-400 mb-4">
            Enterprise-grade security protecting your code and deployments
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm text-slate-500">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-1" />
              Last Updated: August 21, 2025
            </div>
            <div className="flex items-center">
              <ShieldCheck className="h-4 w-4 mr-1" />
              Security Version 2.0
            </div>
          </div>
        </div>

        {/* Security Overview Cards */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="text-center p-4 bg-gradient-to-br from-green-50 to-emerald-100 dark:from-green-900/20 dark:to-emerald-800/20 border-green-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-green-600 rounded-full">
                <Lock className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-green-900 dark:text-green-100">End-to-End Encryption</h3>
              <p className="text-xs text-green-700 dark:text-green-300">AES-256 + TLS 1.3</p>
              <Badge className="bg-green-100 text-green-800 text-xs">Active</Badge>
            </div>
          </Card>
          
          <Card className="text-center p-4 bg-gradient-to-br from-blue-50 to-cyan-100 dark:from-blue-900/20 dark:to-cyan-800/20 border-blue-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-blue-600 rounded-full">
                <Eye className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-blue-900 dark:text-blue-100">24/7 Monitoring</h3>
              <p className="text-xs text-blue-700 dark:text-blue-300">Real-time threat detection</p>
              <Badge className="bg-blue-100 text-blue-800 text-xs">Live</Badge>
            </div>
          </Card>
          
          <Card className="text-center p-4 bg-gradient-to-br from-purple-50 to-violet-100 dark:from-purple-900/20 dark:to-violet-800/20 border-purple-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-purple-600 rounded-full">
                <UserCheck className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-purple-900 dark:text-purple-100">Zero Trust</h3>
              <p className="text-xs text-purple-700 dark:text-purple-300">Multi-factor authentication</p>
              <Badge className="bg-purple-100 text-purple-800 text-xs">Enforced</Badge>
            </div>
          </Card>
          
          <Card className="text-center p-4 bg-gradient-to-br from-red-50 to-pink-100 dark:from-red-900/20 dark:to-pink-800/20 border-red-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-red-600 rounded-full">
                <Bug className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-red-900 dark:text-red-100">Vulnerability Scanning</h3>
              <p className="text-xs text-red-700 dark:text-red-300">Continuous security testing</p>
              <Badge className="bg-red-100 text-red-800 text-xs">Weekly</Badge>
            </div>
          </Card>
        </div>

        {/* Security Architecture */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Network className="h-5 w-5 mr-2" />
              Security Architecture Overview
            </CardTitle>
            <CardDescription>
              Multi-layered security design protecting your applications and data
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              {/* Application Layer */}
              <div className="text-center p-6 bg-gradient-to-b from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg border border-blue-200">
                <Monitor className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Application Layer</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>OWASP Top 10 Protection</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Input validation & sanitization</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>SQL injection prevention</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>XSS & CSRF protection</span>
                  </div>
                </div>
              </div>

              {/* Infrastructure Layer */}
              <div className="text-center p-6 bg-gradient-to-b from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg border border-green-200">
                <Server className="h-12 w-12 text-green-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Infrastructure Layer</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>AWS security controls</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>VPC isolation</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Network segmentation</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>DDoS protection</span>
                  </div>
                </div>
              </div>

              {/* Data Layer */}
              <div className="text-center p-6 bg-gradient-to-b from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg border border-purple-200">
                <Database className="h-12 w-12 text-purple-600 mx-auto mb-4" />
                <h3 className="font-bold text-lg mb-2">Data Layer</h3>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>AES-256 encryption at rest</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>TLS 1.3 in transit</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Database access controls</span>
                  </div>
                  <div className="flex items-center justify-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Automated backups</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Identity & Access Management */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Key className="h-5 w-5 mr-2" />
              Identity & Access Management
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Authentication */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold text-lg mb-3 flex items-center">
                  <Fingerprint className="h-5 w-5 mr-2 text-blue-600" />
                  Authentication Controls
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Multi-Factor Authentication (MFA) enforced</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>AWS Cognito integration</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>OAuth 2.0 / OpenID Connect</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Password complexity requirements</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Account lockout protection</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Session timeout controls</span>
                  </div>
                </div>
              </div>

              {/* Authorization */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold text-lg mb-3 flex items-center">
                  <UserCheck className="h-5 w-5 mr-2 text-green-600" />
                  Authorization & Access Control
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Role-Based Access Control (RBAC)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Principle of least privilege</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Just-in-time access (JIT)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>API key management</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Resource-level permissions</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Regular access reviews</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Protection */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Lock className="h-5 w-5 mr-2" />
              Data Protection & Encryption
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* Encryption Standards */}
            <div className="border rounded-lg p-4 bg-gradient-to-r from-indigo-50 to-purple-50 dark:from-indigo-900/10 dark:to-purple-900/10">
              <h4 className="font-semibold text-lg mb-3 flex items-center">
                <Lock className="h-5 w-5 mr-2 text-indigo-600" />
                Encryption Standards
              </h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div>
                  <h5 className="font-medium mb-2">Data at Rest</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>AES-256-GCM encryption</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>AWS KMS key management</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Envelope encryption</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Key rotation (90 days)</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h5 className="font-medium mb-2">Data in Transit</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>TLS 1.3 encryption</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Perfect Forward Secrecy (PFS)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Certificate pinning</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>HSTS enforcement</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Data Classification */}
            <div className="border rounded-lg p-4">
              <h4 className="font-semibold text-lg mb-3 flex items-center">
                <Archive className="h-5 w-5 mr-2 text-blue-600" />
                Data Classification & Handling
              </h4>
              <div className="grid md:grid-cols-3 gap-4">
                <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded border-red-200 border">
                  <h5 className="font-medium text-red-800 dark:text-red-200 mb-2">Confidential</h5>
                  <div className="text-xs space-y-1">
                    <div>API keys & secrets</div>
                    <div>User credentials</div>
                    <div>Personal data (PII)</div>
                  </div>
                </div>
                <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded border-yellow-200 border">
                  <h5 className="font-medium text-yellow-800 dark:text-yellow-200 mb-2">Internal</h5>
                  <div className="text-xs space-y-1">
                    <div>Application code</div>
                    <div>Configuration files</div>
                    <div>Deployment logs</div>
                  </div>
                </div>
                <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded border-green-200 border">
                  <h5 className="font-medium text-green-800 dark:text-green-200 mb-2">Public</h5>
                  <div className="text-xs space-y-1">
                    <div>Documentation</div>
                    <div>Marketing content</div>
                    <div>Public repositories</div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Infrastructure Security */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <CloudCog className="h-5 w-5 mr-2" />
              Infrastructure Security
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* AWS Security */}
            <div className="border rounded-lg p-4 bg-gradient-to-r from-orange-50 to-red-50 dark:from-orange-900/10 dark:to-red-900/10">
              <h4 className="font-semibold text-lg mb-3 flex items-center">
                <CloudCog className="h-5 w-5 mr-2 text-orange-600" />
                AWS Security Framework
              </h4>
              <div className="grid md:grid-cols-2 gap-6">
                <div>
                  <h5 className="font-medium mb-2">Compute Security</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>EC2 instance hardening</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Container image scanning</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Lambda function isolation</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Auto-scaling security groups</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h5 className="font-medium mb-2">Network Security</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>VPC with private subnets</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Network ACLs & Security Groups</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>NAT Gateway for outbound</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>AWS WAF protection</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Container Security */}
            <div className="border rounded-lg p-4">
              <h4 className="font-semibold text-lg mb-3 flex items-center">
                <Cpu className="h-5 w-5 mr-2 text-blue-600" />
                Container & Deployment Security
              </h4>
              <div className="grid md:grid-cols-3 gap-4">
                <div>
                  <h5 className="font-medium mb-2">Image Security</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Base image scanning</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Vulnerability assessments</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Signed container images</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h5 className="font-medium mb-2">Runtime Security</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Non-root containers</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Resource limits</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Security contexts</span>
                    </div>
                  </div>
                </div>
                <div>
                  <h5 className="font-medium mb-2">Orchestration</h5>
                  <div className="space-y-1 text-sm">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>ECS security groups</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Task isolation</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Secrets management</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Monitoring & Detection */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Eye className="h-5 w-5 mr-2" />
              Security Monitoring & Threat Detection
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Real-time Monitoring */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold text-lg mb-3 flex items-center">
                  <Bell className="h-5 w-5 mr-2 text-green-600" />
                  Real-time Monitoring
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>24/7 security operations center (SOC)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>SIEM (Security Information Event Management)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Automated threat detection</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Behavioral analytics</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Anomaly detection algorithms</span>
                  </div>
                </div>
              </div>

              {/* Incident Response */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold text-lg mb-3 flex items-center">
                  <AlertTriangle className="h-5 w-5 mr-2 text-red-600" />
                  Incident Response
                </h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Automated incident response playbooks</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Mean Time to Detection (MTTD) &lt; 15 minutes</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Mean Time to Response (MTTR) &lt; 1 hour</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Forensic investigation capabilities</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Post-incident analysis & improvement</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Monitoring Tools */}
            <div className="border rounded-lg p-4 bg-slate-50 dark:bg-slate-800/50">
              <h4 className="font-semibold text-lg mb-3">Security Monitoring Stack</h4>
              <div className="grid md:grid-cols-4 gap-3">
                <Badge variant="outline" className="justify-center p-2">
                  <Shield className="h-3 w-3 mr-1" />
                  AWS GuardDuty
                </Badge>
                <Badge variant="outline" className="justify-center p-2">
                  <Eye className="h-3 w-3 mr-1" />
                  AWS CloudTrail
                </Badge>
                <Badge variant="outline" className="justify-center p-2">
                  <Settings className="h-3 w-3 mr-1" />
                  AWS Config
                </Badge>
                <Badge variant="outline" className="justify-center p-2">
                  <Network className="h-3 w-3 mr-1" />
                  VPC Flow Logs
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Testing */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Bug className="h-5 w-5 mr-2" />
              Security Testing & Validation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-3 gap-6">
              {/* Penetration Testing */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold mb-3 flex items-center">
                  <Target className="h-5 w-5 mr-2 text-red-600" />
                  Penetration Testing
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <Timer className="h-3 w-3 text-blue-600 mr-2" />
                    <span>Quarterly external pentests</span>
                  </div>
                  <div className="flex items-center">
                    <Timer className="h-3 w-3 text-blue-600 mr-2" />
                    <span>Annual red team exercises</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>OWASP methodology</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>Remediation tracking</span>
                  </div>
                </div>
              </div>

              {/* Vulnerability Scanning */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold mb-3 flex items-center">
                  <Bug className="h-5 w-5 mr-2 text-orange-600" />
                  Vulnerability Management
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <Timer className="h-3 w-3 text-blue-600 mr-2" />
                    <span>Weekly vulnerability scans</span>
                  </div>
                  <div className="flex items-center">
                    <Timer className="h-3 w-3 text-blue-600 mr-2" />
                    <span>Daily dependency checks</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>Automated patching</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>Risk-based prioritization</span>
                  </div>
                </div>
              </div>

              {/* Code Security */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold mb-3 flex items-center">
                  <FileText className="h-5 w-5 mr-2 text-purple-600" />
                  Secure Development
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>Static code analysis (SAST)</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>Dynamic testing (DAST)</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>Dependency scanning (SCA)</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                    <span>Security code reviews</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Business Continuity */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <HardDrive className="h-5 w-5 mr-2" />
              Business Continuity & Disaster Recovery
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div className="grid md:grid-cols-2 gap-6">
              {/* Backup Strategy */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold mb-3 flex items-center">
                  <Archive className="h-5 w-5 mr-2 text-blue-600" />
                  Backup & Recovery
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Automated daily backups</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Multi-region backup storage</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Point-in-time recovery (PITR)</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Backup encryption & integrity verification</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Monthly restore testing</span>
                  </div>
                </div>
              </div>

              {/* High Availability */}
              <div className="border rounded-lg p-4">
                <h4 className="font-semibold mb-3 flex items-center">
                  <Wifi className="h-5 w-5 mr-2 text-green-600" />
                  High Availability
                </h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>99.9% uptime SLA</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Multi-AZ deployment</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Auto-scaling & load balancing</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Automated failover mechanisms</span>
                  </div>
                  <div className="flex items-center">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Real-time health monitoring</span>
                  </div>
                </div>
              </div>
            </div>

            {/* RTO/RPO Targets */}
            <div className="border rounded-lg p-4 bg-gradient-to-r from-green-50 to-blue-50 dark:from-green-900/10 dark:to-blue-900/10">
              <h4 className="font-semibold mb-3">Recovery Objectives</h4>
              <div className="grid md:grid-cols-2 gap-4">
                <div className="text-center p-3 bg-white dark:bg-slate-800 rounded border">
                  <div className="text-2xl font-bold text-green-600 mb-1">&lt; 4 hours</div>
                  <div className="text-sm font-medium">Recovery Time Objective (RTO)</div>
                  <div className="text-xs text-slate-600 dark:text-slate-400">Maximum acceptable downtime</div>
                </div>
                <div className="text-center p-3 bg-white dark:bg-slate-800 rounded border">
                  <div className="text-2xl font-bold text-blue-600 mb-1">&lt; 1 hour</div>
                  <div className="text-sm font-medium">Recovery Point Objective (RPO)</div>
                  <div className="text-xs text-slate-600 dark:text-slate-400">Maximum acceptable data loss</div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Certifications */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Award className="h-5 w-5 mr-2" />
              Security Certifications & Compliance
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-4 gap-4 mb-6">
              <div className="text-center p-4 bg-gradient-to-b from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
                <Shield className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <h4 className="font-semibold">SOC 2 Type II</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">In Progress</p>
              </div>
              <div className="text-center p-4 bg-gradient-to-b from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
                <Globe className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <h4 className="font-semibold">ISO 27001</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">Planned 2026</p>
              </div>
              <div className="text-center p-4 bg-gradient-to-b from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg">
                <Scale className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                <h4 className="font-semibold">GDPR</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">Compliant</p>
              </div>
              <div className="text-center p-4 bg-gradient-to-b from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 rounded-lg">
                <Heart className="h-8 w-8 text-red-600 mx-auto mb-2" />
                <h4 className="font-semibold">HIPAA</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">BAA Available</p>
              </div>
            </div>
            
            <Alert className="bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
              <ShieldCheck className="h-4 w-4 text-blue-600" />
              <AlertDescription className="text-blue-800 dark:text-blue-200">
                <strong>Security Documentation:</strong> Request security questionnaires, SOC reports, 
                and compliance documentation at 
                <a href="mailto:security@claydesk.com" className="font-medium underline ml-1">security@claydesk.com</a>
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>

        {/* Security Contact */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Mail className="h-5 w-5 mr-2" />
              Security Contact & Reporting
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Security Team</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <Mail className="h-4 w-4 mr-2" />
                    <span>security@claydesk.com</span>
                  </div>
                  <div className="flex items-center">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    <span>security-incidents@claydesk.com</span>
                  </div>
                  <div className="flex items-center">
                    <Bug className="h-4 w-4 mr-2" />
                    <span>security-research@claydesk.com</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Vulnerability Disclosure</h4>
                <div className="space-y-1 text-sm text-slate-600 dark:text-slate-400">
                  <p>We welcome responsible security research and disclosure.</p>
                  <p>Please report vulnerabilities to our security team.</p>
                  <p>Response time: &lt; 24 hours for critical issues</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            This security page details our current security measures and is updated regularly.
          </p>
          <p className="mt-2">
            Related documents: <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a> • 
            <a href="/terms" className="text-blue-600 hover:underline ml-1">Terms of Service</a> • 
            <a href="/compliance" className="text-blue-600 hover:underline ml-1">Compliance</a> •
            <a href="/cookies" className="text-blue-600 hover:underline ml-1">Cookie Policy</a>
          </p>
          <p className="mt-4 font-semibold">
            Last updated: August 21, 2025 | Security inquiries: security@claydesk.com
          </p>
        </div>
      </div>
    </div>
  )
}
