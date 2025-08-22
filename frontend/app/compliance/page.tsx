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
  Flag
} from 'lucide-react'

export default function CompliancePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-6xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Shield className="h-12 w-12 text-green-600 mr-3" />
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100">
              Compliance & Security
            </h1>
          </div>
          <p className="text-xl text-slate-600 dark:text-slate-400 mb-4">
            CodeFlowOps Platform Security Standards and Regulatory Compliance
          </p>
          <div className="flex items-center justify-center space-x-4 text-sm text-slate-500">
            <div className="flex items-center">
              <Calendar className="h-4 w-4 mr-1" />
              Last Updated: August 21, 2025
            </div>
            <div className="flex items-center">
              <FileText className="h-4 w-4 mr-1" />
              Version 1.0
            </div>
          </div>
        </div>

        {/* Compliance Badges */}
        <div className="grid md:grid-cols-4 gap-4 mb-8">
          <Card className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 border-blue-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-blue-600 rounded-full">
                <Scale className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-blue-900 dark:text-blue-100">GDPR</h3>
              <p className="text-xs text-blue-700 dark:text-blue-300">EU Compliant</p>
              <Badge className="bg-green-100 text-green-800 text-xs">✓ Certified</Badge>
            </div>
          </Card>
          
          <Card className="text-center p-4 bg-gradient-to-br from-red-50 to-red-100 dark:from-red-900/20 dark:to-red-800/20 border-red-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-red-600 rounded-full">
                <Heart className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-red-900 dark:text-red-100">HIPAA</h3>
              <p className="text-xs text-red-700 dark:text-red-300">Healthcare Ready</p>
              <Badge className="bg-green-100 text-green-800 text-xs">✓ BAA Available</Badge>
            </div>
          </Card>
          
          <Card className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 border-purple-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-purple-600 rounded-full">
                <Flag className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-purple-900 dark:text-purple-100">CCPA</h3>
              <p className="text-xs text-purple-700 dark:text-purple-300">California Ready</p>
              <Badge className="bg-green-100 text-green-800 text-xs">✓ Compliant</Badge>
            </div>
          </Card>
          
          <Card className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 border-yellow-200">
            <div className="flex flex-col items-center space-y-2">
              <div className="p-3 bg-yellow-600 rounded-full">
                <Award className="h-6 w-6 text-white" />
              </div>
              <h3 className="font-bold text-yellow-900 dark:text-yellow-100">SOC 2</h3>
              <p className="text-xs text-yellow-700 dark:text-yellow-300">Type II Ready</p>
              <Badge className="bg-blue-100 text-blue-800 text-xs">In Progress</Badge>
            </div>
          </Card>
        </div>

        {/* Compliance Overview */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Target className="h-5 w-5 mr-2" />
              Compliance Overview
            </CardTitle>
            <CardDescription>
              Our commitment to security, privacy, and regulatory compliance
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              CodeFlowOps is committed to maintaining the highest standards of security and compliance. 
              We implement comprehensive security controls and adhere to industry best practices to protect 
              your data and ensure regulatory compliance.
            </p>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <Shield className="h-8 w-8 text-green-600 mx-auto mb-2" />
                <h4 className="font-semibold">Security First</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Enterprise-grade security controls
                </p>
              </div>
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <Globe className="h-8 w-8 text-blue-600 mx-auto mb-2" />
                <h4 className="font-semibold">Global Compliance</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  GDPR, CCPA, SOC 2 Type II ready
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <Eye className="h-8 w-8 text-purple-600 mx-auto mb-2" />
                <h4 className="font-semibold">Transparency</h4>
                <p className="text-sm text-slate-600 dark:text-slate-400">
                  Regular audits and reporting
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Compliance Certifications & Badges */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Award className="h-5 w-5 mr-2" />
              Compliance Certifications & Standards
            </CardTitle>
            <CardDescription>
              Official certifications and compliance standards we adhere to
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-3 gap-6">
              {/* Healthcare Compliance */}
              <div className="text-center space-y-4">
                <div className="mx-auto w-24 h-24 bg-gradient-to-br from-red-500 to-pink-600 rounded-full flex items-center justify-center shadow-lg">
                  <Heart className="h-12 w-12 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">HIPAA Ready</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Healthcare compliance with Business Associate Agreement
                  </p>
                  <Badge className="bg-green-100 text-green-800">BAA Available</Badge>
                </div>
              </div>
              
              {/* EU Compliance */}
              <div className="text-center space-y-4">
                <div className="mx-auto w-24 h-24 bg-gradient-to-br from-blue-500 to-indigo-600 rounded-full flex items-center justify-center shadow-lg">
                  <Scale className="h-12 w-12 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">GDPR Certified</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    EU data protection with full data subject rights
                  </p>
                  <Badge className="bg-green-100 text-green-800">Fully Compliant</Badge>
                </div>
              </div>
              
              {/* Security Standards */}
              <div className="text-center space-y-4">
                <div className="mx-auto w-24 h-24 bg-gradient-to-br from-yellow-500 to-orange-600 rounded-full flex items-center justify-center shadow-lg">
                  <Shield className="h-12 w-12 text-white" />
                </div>
                <div>
                  <h3 className="font-bold text-lg">SOC 2 Type II</h3>
                  <p className="text-sm text-slate-600 dark:text-slate-400 mb-2">
                    Security, availability, and confidentiality controls
                  </p>
                  <Badge className="bg-blue-100 text-blue-800">In Progress</Badge>
                </div>
              </div>
            </div>
            
            {/* Additional Certifications Row */}
            <div className="mt-8 pt-6 border-t">
              <h4 className="font-semibold mb-4 text-center">Additional Standards & Frameworks</h4>
              <div className="flex flex-wrap justify-center gap-3">
                <Badge variant="outline" className="px-3 py-1">
                  <Flag className="h-3 w-3 mr-1" />
                  CCPA/CPRA
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <Shield className="h-3 w-3 mr-1" />
                  NIST CSF
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <Globe className="h-3 w-3 mr-1" />
                  ISO 27001 (Planned)
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <Zap className="h-3 w-3 mr-1" />
                  OWASP Top 10
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <CloudCog className="h-3 w-3 mr-1" />
                  AWS Well-Architected
                </Badge>
                <Badge variant="outline" className="px-3 py-1">
                  <Users className="h-3 w-3 mr-1" />
                  FERPA Ready
                </Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Security Frameworks */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Lock className="h-5 w-5 mr-2" />
              Security Frameworks & Standards
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* SOC 2 Type II */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Crown className="h-5 w-5 text-yellow-600" />
                  <h4 className="font-semibold text-lg">SOC 2 Type II</h4>
                  <Badge className="bg-green-100 text-green-800">In Progress</Badge>
                </div>
                <Button variant="outline" size="sm">
                  <Download className="h-4 w-4 mr-2" />
                  Request Report
                </Button>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                System and Organization Controls (SOC) 2 Type II audit covering Security, 
                Availability, Processing Integrity, Confidentiality, and Privacy.
              </p>
              <div className="grid md:grid-cols-5 gap-2">
                <Badge variant="outline" className="text-center">Security</Badge>
                <Badge variant="outline" className="text-center">Availability</Badge>
                <Badge variant="outline" className="text-center">Processing Integrity</Badge>
                <Badge variant="outline" className="text-center">Confidentiality</Badge>
                <Badge variant="outline" className="text-center">Privacy</Badge>
              </div>
            </div>

            {/* ISO 27001 */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Globe className="h-5 w-5 text-blue-600" />
                  <h4 className="font-semibold text-lg">ISO 27001</h4>
                  <Badge className="bg-blue-100 text-blue-800">Planned</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                International standard for information security management systems (ISMS). 
                Planned certification for comprehensive security management.
              </p>
              <div className="text-xs text-slate-500">
                Expected certification: Q2 2026
              </div>
            </div>

            {/* NIST Cybersecurity Framework */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Shield className="h-5 w-5 text-green-600" />
                  <h4 className="font-semibold text-lg">NIST Cybersecurity Framework</h4>
                  <Badge className="bg-green-100 text-green-800">Implemented</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                Following NIST CSF guidelines for cybersecurity risk management across 
                Identify, Protect, Detect, Respond, and Recover functions.
              </p>
              <div className="grid md:grid-cols-5 gap-2">
                <Badge variant="secondary" className="text-center">Identify</Badge>
                <Badge variant="secondary" className="text-center">Protect</Badge>
                <Badge variant="secondary" className="text-center">Detect</Badge>
                <Badge variant="secondary" className="text-center">Respond</Badge>
                <Badge variant="secondary" className="text-center">Recover</Badge>
              </div>
            </div>

            {/* OWASP Top 10 */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Zap className="h-5 w-5 text-red-600" />
                  <h4 className="font-semibold text-lg">OWASP Top 10</h4>
                  <Badge className="bg-green-100 text-green-800">Compliant</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                Application security practices following OWASP Top 10 guidelines for 
                web application security vulnerabilities.
              </p>
              <div className="text-xs text-slate-500">
                Regular security assessments and penetration testing
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Data Privacy Compliance */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Data Privacy Compliance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* GDPR */}
            <div className="border rounded-lg p-6 bg-gradient-to-r from-blue-50 to-indigo-50 dark:from-blue-900/10 dark:to-indigo-900/10">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-blue-600 rounded-full">
                    <Scale className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-xl">GDPR (General Data Protection Regulation)</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400">EU Data Protection Compliance</p>
                  </div>
                  <Badge className="bg-green-100 text-green-800 ml-auto">Fully Compliant</Badge>
                </div>
                <Button variant="outline" size="sm" className="border-blue-300 text-blue-700 hover:bg-blue-50">
                  <Download className="h-4 w-4 mr-2" />
                  Request DPA
                </Button>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                Full compliance with EU General Data Protection Regulation for processing personal data of EU residents. 
                We serve as both Data Controller and Data Processor depending on the service context.
              </p>
              
              {/* GDPR Principles */}
              <div className="grid md:grid-cols-2 gap-4 mb-4">
                <div className="bg-white dark:bg-slate-800 p-4 rounded-lg border">
                  <h5 className="font-semibold text-sm mb-3 flex items-center">
                    <Verified className="h-4 w-4 mr-1 text-blue-600" />
                    GDPR Principles Implemented
                  </h5>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Lawfulness, fairness and transparency</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Purpose limitation</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Data minimization</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Accuracy</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Storage limitation</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Integrity and confidentiality</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Accountability</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white dark:bg-slate-800 p-4 rounded-lg border">
                  <h5 className="font-semibold text-sm mb-3 flex items-center">
                    <Users className="h-4 w-4 mr-1 text-blue-600" />
                    Data Subject Rights
                  </h5>
                  <div className="space-y-2 text-xs">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Right to be informed</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Right of access (Art. 15)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Right to rectification (Art. 16)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Right to erasure (Art. 17)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Right to restrict processing (Art. 18)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Right to data portability (Art. 20)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Right to object (Art. 21)</span>
                    </div>
                  </div>
                </div>
              </div>
              
              {/* GDPR Compliance Features */}
              <div className="bg-white dark:bg-slate-800 p-4 rounded-lg border mb-4">
                <h5 className="font-semibold text-sm mb-3 flex items-center">
                  <Settings className="h-4 w-4 mr-1 text-blue-600" />
                  GDPR Compliance Features
                </h5>
                <div className="grid md:grid-cols-2 gap-4 text-xs">
                  <div className="space-y-1">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Privacy by Design and by Default</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Data Protection Impact Assessments (DPIA)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Data Processing Records (Art. 30)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>72-hour breach notification</span>
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Consent management system</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Automated data subject request handling</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Cross-border transfer safeguards</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-2" />
                      <span>Data retention policy automation</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <Alert className="bg-blue-50 border-blue-200 dark:bg-blue-900/20 dark:border-blue-800">
                <Scale className="h-4 w-4 text-blue-600" />
                <AlertDescription className="text-blue-800 dark:text-blue-200">
                  <strong>EU Data Processing:</strong> We provide Data Processing Agreements (DPA) and maintain 
                  Standard Contractual Clauses (SCCs) for international transfers. Contact 
                  <a href="mailto:gdpr@claydesk.com" className="font-medium underline ml-1">gdpr@claydesk.com</a> 
                  for EU-specific compliance documentation.
                </AlertDescription>
              </Alert>
            </div>

            {/* CCPA/CPRA */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Star className="h-5 w-5 text-purple-600" />
                  <h4 className="font-semibold text-lg">CCPA/CPRA (California Consumer Privacy Act)</h4>
                  <Badge className="bg-green-100 text-green-800">Compliant</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                Compliance with California Consumer Privacy Act and California Privacy Rights Act 
                for California residents.
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>Right to know about personal information collection</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>Right to delete personal information</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>Right to opt-out of sale/sharing (We do not sell data)</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>Right to correct inaccurate personal information</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>Right to limit use of sensitive personal information</span>
                </div>
              </div>
            </div>

            {/* Other State Privacy Laws */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Building className="h-5 w-5 text-green-600" />
                  <h4 className="font-semibold text-lg">US State Privacy Laws</h4>
                  <Badge className="bg-green-100 text-green-800">Compliant</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                Compliance with emerging state privacy laws across the United States.
              </p>
              <div className="grid md:grid-cols-2 gap-2">
                <Badge variant="outline">Virginia (VCDPA)</Badge>
                <Badge variant="outline">Colorado (CPA)</Badge>
                <Badge variant="outline">Connecticut (CTDPA)</Badge>
                <Badge variant="outline">Utah (UCPA)</Badge>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Industry-Specific Compliance */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Gavel className="h-5 w-5 mr-2" />
              Industry-Specific Compliance
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* HIPAA */}
            <div className="border rounded-lg p-6 bg-gradient-to-r from-red-50 to-pink-50 dark:from-red-900/10 dark:to-pink-900/10">
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-3">
                  <div className="p-2 bg-red-600 rounded-full">
                    <Heart className="h-6 w-6 text-white" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-xl">HIPAA (Health Insurance Portability and Accountability Act)</h4>
                    <p className="text-sm text-slate-600 dark:text-slate-400">Healthcare Data Protection Compliance</p>
                  </div>
                  <Badge className="bg-green-100 text-green-800 ml-auto">BAA Available</Badge>
                </div>
                <Button variant="outline" size="sm" className="border-red-300 text-red-700 hover:bg-red-50">
                  <Download className="h-4 w-4 mr-2" />
                  Request BAA
                </Button>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-4">
                Business Associate Agreement (BAA) available for healthcare organizations handling Protected Health Information (PHI). 
                CodeFlowOps implements comprehensive HIPAA safeguards for administrative, physical, and technical security.
              </p>
              
              {/* HIPAA Safeguards */}
              <div className="grid md:grid-cols-3 gap-4 mb-4">
                <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border">
                  <h5 className="font-semibold text-sm mb-2 flex items-center">
                    <Shield className="h-4 w-4 mr-1 text-red-600" />
                    Administrative Safeguards
                  </h5>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Security Officer designation</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Workforce training programs</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Access management procedures</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Incident response procedures</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border">
                  <h5 className="font-semibold text-sm mb-2 flex items-center">
                    <Building className="h-4 w-4 mr-1 text-red-600" />
                    Physical Safeguards
                  </h5>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Facility access controls</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Workstation security</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Device and media controls</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Data center security (AWS)</span>
                    </div>
                  </div>
                </div>
                
                <div className="bg-white dark:bg-slate-800 p-3 rounded-lg border">
                  <h5 className="font-semibold text-sm mb-2 flex items-center">
                    <Lock className="h-4 w-4 mr-1 text-red-600" />
                    Technical Safeguards
                  </h5>
                  <div className="space-y-1 text-xs">
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Access control (MFA)</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Audit controls and logging</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Data integrity controls</span>
                    </div>
                    <div className="flex items-center">
                      <CheckCircle className="h-3 w-3 text-green-600 mr-1" />
                      <span>Transmission security (TLS 1.3)</span>
                    </div>
                  </div>
                </div>
              </div>
              
              <Alert className="bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800">
                <Heart className="h-4 w-4 text-red-600" />
                <AlertDescription className="text-red-800 dark:text-red-200">
                  <strong>Healthcare Organizations:</strong> Contact our compliance team at 
                  <a href="mailto:hipaa@claydesk.com" className="font-medium underline ml-1">hipaa@claydesk.com</a> 
                  to request a Business Associate Agreement and enable HIPAA-compliant features.
                </AlertDescription>
              </Alert>
            </div>

            {/* PCI DSS */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <CreditCard className="h-5 w-5 text-blue-600" />
                  <h4 className="font-semibold text-lg">PCI DSS (Payment Card Industry Data Security Standard)</h4>
                  <Badge className="bg-gray-100 text-gray-800">Not Applicable</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                CodeFlowOps does not process, store, or transmit payment card information. 
                Payment processing is handled by certified third-party processors.
              </p>
            </div>

            {/* FERPA */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Users className="h-5 w-5 text-green-600" />
                  <h4 className="font-semibold text-lg">FERPA (Family Educational Rights and Privacy Act)</h4>
                  <Badge className="bg-green-100 text-green-800">Ready</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                Appropriate safeguards for educational institutions handling student records. 
                Data Processing Agreements available for educational use cases.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Cloud Security */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <CloudCog className="h-5 w-5 mr-2" />
              Cloud Security & Infrastructure
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            {/* AWS Security */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <CloudCog className="h-5 w-5 text-orange-600" />
                  <h4 className="font-semibold text-lg">AWS Security Best Practices</h4>
                  <Badge className="bg-green-100 text-green-800">Implemented</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                Leveraging AWS security controls and best practices for cloud infrastructure security.
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>AWS Well-Architected Framework Security Pillar</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>AWS Config for compliance monitoring</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>AWS CloudTrail for audit logging</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>AWS IAM least privilege access</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>VPC security groups and NACLs</span>
                </div>
              </div>
            </div>

            {/* Encryption */}
            <div className="border rounded-lg p-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center space-x-2">
                  <Lock className="h-5 w-5 text-purple-600" />
                  <h4 className="font-semibold text-lg">Encryption Standards</h4>
                  <Badge className="bg-green-100 text-green-800">AES-256</Badge>
                </div>
              </div>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-3">
                Industry-standard encryption for data protection at rest and in transit.
              </p>
              <div className="space-y-2">
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>TLS 1.3 for data in transit</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>AES-256 encryption for data at rest</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>AWS KMS for key management</span>
                </div>
                <div className="flex items-center text-sm">
                  <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                  <span>Perfect Forward Secrecy (PFS)</span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Access Controls & Authentication */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Access Controls & Authentication
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Identity Management</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Multi-factor authentication (MFA)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Single Sign-On (SSO) support</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>OAuth 2.0 / OpenID Connect</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Role-based access control (RBAC)</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Session Management</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Secure session tokens</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Session timeout controls</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Concurrent session limits</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Secure logout procedures</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Monitoring & Incident Response */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Eye className="h-5 w-5 mr-2" />
              Monitoring & Incident Response
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Security Monitoring</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>24/7 security monitoring</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Real-time threat detection</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Automated alerting systems</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Security Information and Event Management (SIEM)</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Incident Response</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Incident response plan</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Breach notification procedures</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Forensic investigation capabilities</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Post-incident review and improvement</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Vendor & Supply Chain Security */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Building className="h-5 w-5 mr-2" />
              Vendor & Supply Chain Security
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              We maintain strict security standards for all vendors and third-party integrations.
            </p>
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Vendor Assessment</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Security questionnaires</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Compliance certifications review</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Data Processing Agreements (DPA)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Regular security reviews</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Key Vendors</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <Badge variant="outline" className="mr-2">SOC 2</Badge>
                    <span>Amazon Web Services (AWS)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Badge variant="outline" className="mr-2">SOC 2</Badge>
                    <span>GitHub (Microsoft)</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Badge variant="outline" className="mr-2">PCI DSS</Badge>
                    <span>Payment Processors</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Badge variant="outline" className="mr-2">ISO 27001</Badge>
                    <span>Monitoring Services</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Business Continuity & Disaster Recovery */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Settings className="h-5 w-5 mr-2" />
              Business Continuity & Disaster Recovery
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Backup & Recovery</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Automated daily backups</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Multi-region backup storage</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Point-in-time recovery</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Regular backup testing</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Service Availability</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>99.9% uptime SLA</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Load balancing and auto-scaling</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Failover mechanisms</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <CheckCircle className="h-4 w-4 text-green-600 mr-2" />
                    <span>Status page and notifications</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Audit & Assessments */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Audit & Security Assessments
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Internal Audits</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <Calendar className="h-4 w-4 text-blue-600 mr-2" />
                    <span>Quarterly security assessments</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Calendar className="h-4 w-4 text-blue-600 mr-2" />
                    <span>Annual compliance reviews</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Calendar className="h-4 w-4 text-blue-600 mr-2" />
                    <span>Continuous monitoring</span>
                  </div>
                </div>
              </div>
              <div>
                <h4 className="font-semibold mb-2">External Assessments</h4>
                <div className="space-y-2">
                  <div className="flex items-center text-sm">
                    <Calendar className="h-4 w-4 text-green-600 mr-2" />
                    <span>Annual penetration testing</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Calendar className="h-4 w-4 text-green-600 mr-2" />
                    <span>Third-party security audits</span>
                  </div>
                  <div className="flex items-center text-sm">
                    <Calendar className="h-4 w-4 text-green-600 mr-2" />
                    <span>Vulnerability assessments</span>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Training & Awareness */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              Security Training & Awareness
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              All employees receive comprehensive security training and regular updates on security best practices.
            </p>
            <div className="grid md:grid-cols-3 gap-4">
              <div className="text-center p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                <Users className="h-6 w-6 text-blue-600 mx-auto mb-2" />
                <h4 className="font-semibold text-sm">Security Onboarding</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Mandatory for all new employees
                </p>
              </div>
              <div className="text-center p-4 bg-green-50 dark:bg-green-900/20 rounded-lg">
                <Calendar className="h-6 w-6 text-green-600 mx-auto mb-2" />
                <h4 className="font-semibold text-sm">Annual Training</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Updated security awareness training
                </p>
              </div>
              <div className="text-center p-4 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                <AlertTriangle className="h-6 w-6 text-purple-600 mx-auto mb-2" />
                <h4 className="font-semibold text-sm">Phishing Simulation</h4>
                <p className="text-xs text-slate-600 dark:text-slate-400">
                  Regular phishing awareness tests
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Compliance Documentation */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Download className="h-5 w-5 mr-2" />
              Compliance Documentation
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Request compliance documentation and certifications for your organization.
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <Button variant="outline" className="h-auto p-4 flex flex-col items-start">
                <div className="flex items-center mb-2">
                  <FileText className="h-4 w-4 mr-2" />
                  <span className="font-semibold">SOC 2 Type II Report</span>
                </div>
                <span className="text-xs text-slate-600 dark:text-slate-400">
                  System and Organization Controls audit report
                </span>
              </Button>
              
              <Button variant="outline" className="h-auto p-4 flex flex-col items-start">
                <div className="flex items-center mb-2">
                  <Shield className="h-4 w-4 mr-2" />
                  <span className="font-semibold">Security Questionnaire</span>
                </div>
                <span className="text-xs text-slate-600 dark:text-slate-400">
                  Standard security assessment responses
                </span>
              </Button>
              
              <Button variant="outline" className="h-auto p-4 flex flex-col items-start">
                <div className="flex items-center mb-2">
                  <Gavel className="h-4 w-4 mr-2" />
                  <span className="font-semibold">Data Processing Agreement</span>
                </div>
                <span className="text-xs text-slate-600 dark:text-slate-400">
                  GDPR-compliant DPA template
                </span>
              </Button>
              
              <Button variant="outline" className="h-auto p-4 flex flex-col items-start">
                <div className="flex items-center mb-2">
                  <Users className="h-4 w-4 mr-2" />
                  <span className="font-semibold">Business Associate Agreement</span>
                </div>
                <span className="text-xs text-slate-600 dark:text-slate-400">
                  HIPAA-compliant BAA for healthcare
                </span>
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Contact & Support */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Mail className="h-5 w-5 mr-2" />
              Compliance Contact & Support
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-600 dark:text-slate-400">
              For compliance questions, security inquiries, or to request documentation, please contact our compliance team.
            </p>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Security & Compliance Team</h4>
                <div className="space-y-2 text-sm">
                  <div className="flex items-center">
                    <Mail className="h-4 w-4 mr-2" />
                    <span>security@claydesk.com</span>
                  </div>
                  <div className="flex items-center">
                    <Shield className="h-4 w-4 mr-2" />
                    <span>compliance@claydesk.com</span>
                  </div>
                  <div className="flex items-center">
                    <AlertTriangle className="h-4 w-4 mr-2" />
                    <span>privacy@claydesk.com</span>
                  </div>
                  <div className="flex items-center">
                    <Heart className="h-4 w-4 mr-2 text-red-600" />
                    <span>hipaa@claydesk.com</span>
                  </div>
                  <div className="flex items-center">
                    <Scale className="h-4 w-4 mr-2 text-blue-600" />
                    <span>gdpr@claydesk.com</span>
                  </div>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Business Information</h4>
                <div className="space-y-1 text-sm">
                  <div className="flex items-start">
                    <MapPin className="h-4 w-4 mr-2 mt-1 flex-shrink-0" />
                    <div>
                      ClayDesk LLC<br />
                      45 Burgundy Hills Lane<br />
                      Middletown, CT 06457<br />
                      United States
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            This compliance page is updated regularly to reflect our current security posture and certifications.
          </p>
          <p className="mt-2">
            Related documents: <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a> • 
            <a href="/terms" className="text-blue-600 hover:underline ml-1">Terms of Service</a> • 
            <a href="/cookies" className="text-blue-600 hover:underline ml-1">Cookie Policy</a>
          </p>
          <p className="mt-4 font-semibold">
            Last updated: August 21, 2025 | For compliance inquiries: compliance@claydesk.com
          </p>
        </div>
      </div>
    </div>
  )
}
