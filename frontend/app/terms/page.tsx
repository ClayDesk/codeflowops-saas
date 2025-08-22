'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { Scale, Calendar, FileText, AlertTriangle, Shield, Users, CreditCard, Globe, Lock, Gavel, Mail, MapPin } from 'lucide-react'

export default function TermsOfServicePage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Scale className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100">
              Terms of Service
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

        {/* Important Notice */}
        <Alert className="mb-8">
          <AlertTriangle className="h-4 w-4" />
          <AlertDescription>
            <strong>Important:</strong> These Terms of Service constitute a legally binding agreement between you and ClayDesk LLC. 
            By using CodeFlowOps, you agree to be bound by these terms. Please read them carefully.
          </AlertDescription>
        </Alert>

        {/* Table of Contents */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Table of Contents</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-2 text-sm">
              <div className="space-y-1">
                <a href="#acceptance" className="block text-blue-600 hover:underline">1. Acceptance of Terms</a>
                <a href="#description" className="block text-blue-600 hover:underline">2. Description of Service</a>
                <a href="#eligibility" className="block text-blue-600 hover:underline">3. Eligibility</a>
                <a href="#accounts" className="block text-blue-600 hover:underline">4. User Accounts</a>
                <a href="#acceptable-use" className="block text-blue-600 hover:underline">5. Acceptable Use Policy</a>
                <a href="#content" className="block text-blue-600 hover:underline">6. User Content</a>
                <a href="#intellectual-property" className="block text-blue-600 hover:underline">7. Intellectual Property</a>
                <a href="#privacy" className="block text-blue-600 hover:underline">8. Privacy</a>
                <a href="#billing" className="block text-blue-600 hover:underline">9. Billing and Payments</a>
                <a href="#termination" className="block text-blue-600 hover:underline">10. Termination</a>
              </div>
              <div className="space-y-1">
                <a href="#disclaimers" className="block text-blue-600 hover:underline">11. Disclaimers</a>
                <a href="#limitation" className="block text-blue-600 hover:underline">12. Limitation of Liability</a>
                <a href="#indemnification" className="block text-blue-600 hover:underline">13. Indemnification</a>
                <a href="#no-responsibility" className="block text-blue-600 hover:underline">14. Complete Disclaimer of Responsibility</a>
                <a href="#third-party" className="block text-blue-600 hover:underline">15. Third-Party Services</a>
                <a href="#governing-law" className="block text-blue-600 hover:underline">16. Governing Law</a>
                <a href="#dispute-resolution" className="block text-blue-600 hover:underline">17. Dispute Resolution</a>
                <a href="#changes" className="block text-blue-600 hover:underline">18. Changes to Terms</a>
                <a href="#contact" className="block text-blue-600 hover:underline">19. Contact Information</a>
                <a href="#miscellaneous" className="block text-blue-600 hover:underline">20. Miscellaneous</a>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section 1: Acceptance of Terms */}
        <Card className="mb-8" id="acceptance">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Gavel className="h-5 w-5 mr-2" />
              1. Acceptance of Terms
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              By accessing or using the CodeFlowOps platform ("Service"), you agree to be bound by these Terms of Service ("Terms"). 
              If you disagree with any part of these terms, then you may not access the Service.
            </p>
            <p>
              These Terms apply to all visitors, users, and others who access or use the Service. 
              If you are using the Service on behalf of a company or organization, you represent that you have the authority to bind that entity to these Terms.
            </p>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                <strong>Service Provider:</strong> ClayDesk LLC, a limited liability company organized under the laws of Connecticut, USA.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 2: Description of Service */}
        <Card className="mb-8" id="description">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Globe className="h-5 w-5 mr-2" />
              2. Description of Service
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              CodeFlowOps is a deployment automation platform that provides the following services:
            </p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Automated analysis and building of static and React front-end applications</li>
              <li>Deployment to customer-owned AWS infrastructure (S3, CloudFront, Amplify Hosting)</li>
              <li>Repository integration with version control systems (GitHub, GitLab, etc.)</li>
              <li>Build pipeline automation and monitoring</li>
              <li>Team collaboration and deployment management tools</li>
            </ul>
            <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg">
              <p className="text-amber-800 dark:text-amber-200 text-sm">
                <AlertTriangle className="h-4 w-4 inline mr-1" />
                <strong>Important Limitation:</strong> CodeFlowOps focuses exclusively on front-end deployment automation. 
                We do not host, operate, or provide back-end services or database infrastructure.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 3: Eligibility */}
        <Card className="mb-8" id="eligibility">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              3. Eligibility
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>You must meet the following requirements to use our Service:</p>
            <ul className="list-disc list-inside space-y-2 ml-4">
              <li>Be at least 18 years old or the age of majority in your jurisdiction</li>
              <li>Have the legal capacity to enter into binding contracts</li>
              <li>Not be prohibited from using the Service under applicable laws</li>
              <li>Provide accurate and complete registration information</li>
            </ul>
            <p>
              If you are using the Service on behalf of an organization, you must have the authority to bind that organization to these Terms.
            </p>
          </CardContent>
        </Card>

        {/* Section 4: User Accounts */}
        <Card className="mb-8" id="accounts">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              4. User Accounts
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Account Creation</h4>
              <p className="text-sm">
                To use certain features of the Service, you must create an account. You may create an account by:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Providing an email address and password</li>
                <li>Using OAuth authentication (GitHub, Google)</li>
                <li>Following our account verification process</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Account Security</h4>
              <p className="text-sm">You are responsible for:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Maintaining the confidentiality of your account credentials</li>
                <li>All activities that occur under your account</li>
                <li>Notifying us immediately of any unauthorized access</li>
                <li>Using strong passwords and enabling two-factor authentication when available</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Account Information</h4>
              <p className="text-sm">
                You agree to provide accurate, current, and complete information and to update such information 
                to maintain its accuracy. We may suspend or terminate accounts with inaccurate information.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 5: Acceptable Use Policy */}
        <Card className="mb-8" id="acceptable-use">
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              5. Acceptable Use Policy
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2 text-green-600">✅ Permitted Uses</h4>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Deploy legitimate front-end applications and websites</li>
                <li>Use the Service for lawful business or personal purposes</li>
                <li>Integrate with your own AWS infrastructure</li>
                <li>Collaborate with team members on deployment projects</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2 text-red-600">❌ Prohibited Uses</h4>
              <p className="text-sm mb-2">You may not use the Service to:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Deploy illegal, harmful, or malicious content</li>
                <li>Violate any applicable laws or regulations</li>
                <li>Infringe on intellectual property rights</li>
                <li>Deploy spam, phishing, or fraudulent content</li>
                <li>Attempt to gain unauthorized access to our systems</li>
                <li>Reverse engineer, decompile, or attempt to extract source code</li>
                <li>Use the Service for cryptocurrency mining or similar resource-intensive activities</li>
                <li>Deploy content that violates third-party terms of service</li>
                <li>Share account credentials or allow unauthorized access</li>
              </ul>
            </div>
            
            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
              <p className="text-red-800 dark:text-red-200 text-sm">
                <strong>Enforcement:</strong> Violation of this Acceptable Use Policy may result in immediate suspension 
                or termination of your account without notice.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 6: User Content */}
        <Card className="mb-8" id="content">
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              6. User Content
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Content Ownership</h4>
              <p className="text-sm">
                You retain ownership of all content you submit, upload, or deploy through the Service ("User Content"). 
                You grant us a limited license to process, store, and deploy your content as necessary to provide the Service.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Content Responsibility</h4>
              <p className="text-sm">You are solely responsible for:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>The accuracy, legality, and appropriateness of your User Content</li>
                <li>Ensuring you have the right to use and deploy all content</li>
                <li>Compliance with applicable laws and third-party rights</li>
                <li>Any damages or liability arising from your User Content</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Content Standards</h4>
              <p className="text-sm">Your User Content must not:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Contain illegal, harmful, or offensive material</li>
                <li>Infringe on intellectual property rights</li>
                <li>Contain malware, viruses, or malicious code</li>
                <li>Violate privacy rights or contain unauthorized personal information</li>
                <li>Be used for spam, fraud, or deceptive practices</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Content Removal</h4>
              <p className="text-sm">
                We reserve the right to remove or disable access to any User Content that violates these Terms 
                or is otherwise objectionable, without prior notice.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 7: Intellectual Property */}
        <Card className="mb-8" id="intellectual-property">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Lock className="h-5 w-5 mr-2" />
              7. Intellectual Property
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Our IP Rights</h4>
              <p className="text-sm">
                The Service and its original content, features, and functionality are and will remain the exclusive property 
                of ClayDesk LLC and its licensors. The Service is protected by copyright, trademark, and other laws.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Limited License</h4>
              <p className="text-sm">
                We grant you a limited, non-exclusive, non-transferable, revocable license to use the Service 
                in accordance with these Terms.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Restrictions</h4>
              <p className="text-sm">You may not:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Copy, modify, or distribute our proprietary content</li>
                <li>Reverse engineer or attempt to extract source code</li>
                <li>Use our trademarks without permission</li>
                <li>Create derivative works based on the Service</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">DMCA Compliance</h4>
              <p className="text-sm">
                We respect intellectual property rights. If you believe your copyright has been infringed, 
                please contact us with a DMCA takedown notice at legal@claydesk.com.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 8: Privacy */}
        <Card className="mb-8" id="privacy">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Shield className="h-5 w-5 mr-2" />
              8. Privacy
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              Your privacy is important to us. Our Privacy Policy explains how we collect, use, and protect 
              your information when you use the Service.
            </p>
            <p>
              By using the Service, you agree to the collection and use of information in accordance with our Privacy Policy.
            </p>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                📋 <strong>Privacy Policy:</strong> <a href="/privacy" className="underline">View our complete Privacy Policy</a>
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 9: Billing and Payments */}
        <Card className="mb-8" id="billing">
          <CardHeader>
            <CardTitle className="flex items-center">
              <CreditCard className="h-5 w-5 mr-2" />
              9. Billing and Payments
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Subscription Plans</h4>
              <p className="text-sm">
                CodeFlowOps offers various subscription plans with different features and usage limits. 
                Current pricing is available on our website.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Payment Terms</h4>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Subscription fees are billed in advance on a monthly or annual basis</li>
                <li>All fees are non-refundable except as required by law</li>
                <li>You must provide current, complete payment information</li>
                <li>We use third-party payment processors and do not store credit card information</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Usage-Based Billing</h4>
              <p className="text-sm">
                Some features may be subject to usage-based billing (e.g., build minutes, storage, bandwidth). 
                You will be notified before incurring additional charges.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Changes to Pricing</h4>
              <p className="text-sm">
                We reserve the right to change our pricing with 30 days' notice. 
                Price changes will not affect your current billing cycle.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Suspension for Non-Payment</h4>
              <p className="text-sm">
                We may suspend or terminate your account for non-payment after reasonable notice. 
                You remain responsible for all charges incurred before termination.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 10: Termination */}
        <Card className="mb-8" id="termination">
          <CardHeader>
            <CardTitle>10. Termination</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Termination by You</h4>
              <p className="text-sm">
                You may terminate your account at any time through your account settings or by contacting us. 
                Termination does not relieve you of payment obligations for services already provided.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Termination by Us</h4>
              <p className="text-sm">We may terminate or suspend your account immediately, without notice, for:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Violation of these Terms</li>
                <li>Non-payment of fees</li>
                <li>Illegal or harmful use of the Service</li>
                <li>Extended periods of inactivity</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Effect of Termination</h4>
              <p className="text-sm">Upon termination:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>Your right to use the Service will cease immediately</li>
                <li>We may delete your account and data after a reasonable grace period</li>
                <li>You should export any data you wish to retain</li>
                <li>Deployed applications in your AWS account will not be affected</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Section 11: Disclaimers */}
        <Card className="mb-8" id="disclaimers">
          <CardHeader>
            <CardTitle>11. Disclaimers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-yellow-50 dark:bg-yellow-900/20 p-4 rounded-lg">
              <p className="text-yellow-800 dark:text-yellow-200 text-sm font-semibold mb-2">
                IMPORTANT: PLEASE READ THIS SECTION CAREFULLY
              </p>
              <p className="text-yellow-700 dark:text-yellow-300 text-sm">
                THE SERVICE IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, 
                EITHER EXPRESS OR IMPLIED. CLAYDESK LLC EXPRESSLY DISCLAIMS ALL WARRANTIES AND CONDITIONS.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Complete Disclaimer of Warranties</h4>
              <p className="text-sm">CLAYDESK LLC DISCLAIMS ALL WARRANTIES, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE</li>
                <li>NON-INFRINGEMENT OF THIRD-PARTY RIGHTS</li>
                <li>TITLE, QUIET ENJOYMENT, OR NON-INTERRUPTION</li>
                <li>UNINTERRUPTED, TIMELY, SECURE, OR ERROR-FREE OPERATION</li>
                <li>ACCURACY, RELIABILITY, COMPLETENESS, OR QUALITY OF INFORMATION</li>
                <li>SECURITY, AVAILABILITY, OR PERFORMANCE OF THE SERVICE</li>
                <li>COMPATIBILITY WITH YOUR SYSTEMS OR THIRD-PARTY SERVICES</li>
                <li>THAT THE SERVICE WILL MEET YOUR REQUIREMENTS OR EXPECTATIONS</li>
                <li>THAT ALL ERRORS OR DEFECTS WILL BE CORRECTED</li>
                <li>THAT THE SERVICE IS FREE FROM VIRUSES OR OTHER HARMFUL COMPONENTS</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Responsibility for Results</h4>
              <p className="text-sm">
                CLAYDESK LLC MAKES NO WARRANTY THAT THE SERVICE WILL PRODUCE ANY PARTICULAR RESULTS. 
                YOU ACKNOWLEDGE THAT THE SERVICE MAY NOT PERFORM AS EXPECTED AND YOU USE IT ENTIRELY AT YOUR OWN RISK.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Third-Party Services Disclaimer</h4>
              <p className="text-sm">
                WE ARE NOT RESPONSIBLE FOR AND DISCLAIM ALL LIABILITY RELATING TO THE AVAILABILITY, 
                ACCURACY, RELIABILITY, PERFORMANCE, OR OPERATION OF THIRD-PARTY SERVICES 
                (INCLUDING AWS, GITHUB, GOOGLE, OR ANY OTHER INTEGRATED SERVICES). ANY ISSUES WITH 
                THIRD-PARTY SERVICES ARE SOLELY BETWEEN YOU AND THE THIRD-PARTY PROVIDER.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Technical Support Obligation</h4>
              <p className="text-sm">
                WHILE WE MAY PROVIDE TECHNICAL SUPPORT, WE HAVE NO OBLIGATION TO PROVIDE SUPPORT, 
                MAINTENANCE, UPDATES, OR MODIFICATIONS TO THE SERVICE.
              </p>
            </div>
            
            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
              <p className="text-red-800 dark:text-red-200 text-sm font-semibold mb-2">
                IMPORTANT JURISDICTIONAL NOTE
              </p>
              <p className="text-red-700 dark:text-red-300 text-sm">
                SOME JURISDICTIONS DO NOT ALLOW THE EXCLUSION OF IMPLIED WARRANTIES. 
                IN SUCH JURISDICTIONS, THE ABOVE EXCLUSIONS MAY NOT APPLY TO YOU, 
                BUT SHALL BE LIMITED TO THE MAXIMUM EXTENT PERMITTED BY LAW.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 12: Limitation of Liability */}
        <Card className="mb-8" id="limitation">
          <CardHeader>
            <CardTitle>12. Limitation of Liability</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
              <p className="text-red-800 dark:text-red-200 text-sm font-semibold mb-2">
                COMPLETE LIMITATION OF LIABILITY
              </p>
              <p className="text-red-700 dark:text-red-300 text-sm">
                TO THE MAXIMUM EXTENT PERMITTED BY APPLICABLE LAW, IN NO EVENT SHALL CLAYDESK LLC, 
                ITS OFFICERS, DIRECTORS, EMPLOYEES, AGENTS, AFFILIATES, SUBSIDIARIES, SUCCESSORS, 
                OR ASSIGNS BE LIABLE FOR ANY DAMAGES WHATSOEVER.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Liability for Any Damages</h4>
              <p className="text-sm">CLAYDESK LLC SHALL NOT BE LIABLE FOR ANY:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>DIRECT, INDIRECT, INCIDENTAL, SPECIAL, CONSEQUENTIAL, OR PUNITIVE DAMAGES</li>
                <li>LOSS OF PROFITS, REVENUE, BUSINESS, OR BUSINESS OPPORTUNITIES</li>
                <li>LOSS OF DATA, INFORMATION, OR CONTENT</li>
                <li>LOSS OF USE, INTERRUPTION, OR DELAY IN SERVICE</li>
                <li>SYSTEM DOWNTIME, CRASHES, OR TECHNICAL FAILURES</li>
                <li>SECURITY BREACHES, DATA BREACHES, OR UNAUTHORIZED ACCESS</li>
                <li>ERRORS, BUGS, DEFECTS, OR MALFUNCTIONS IN THE SERVICE</li>
                <li>THIRD-PARTY ACTIONS, SERVICES, OR CONTENT</li>
                <li>DEPLOYMENT FAILURES OR UNSUCCESSFUL BUILDS</li>
                <li>AWS CHARGES, COSTS, OR BILLING ISSUES</li>
                <li>REPUTATION DAMAGE OR LOSS OF GOODWILL</li>
                <li>PERSONAL INJURY OR PROPERTY DAMAGE</li>
                <li>ANY OTHER LOSSES OR DAMAGES OF ANY KIND</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Maximum Liability Cap</h4>
              <p className="text-sm">
                IF, DESPITE THE ABOVE LIMITATIONS, CLAYDESK LLC IS FOUND LIABLE FOR ANY DAMAGES, 
                OUR TOTAL AGGREGATE LIABILITY SHALL NOT EXCEED THE LESSER OF:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>THE TOTAL AMOUNT YOU PAID TO US IN THE 12 MONTHS PRECEDING THE CLAIM</li>
                <li>ONE HUNDRED DOLLARS ($100 USD)</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Basis of Bargain</h4>
              <p className="text-sm">
                THESE LIMITATIONS OF LIABILITY ARE AN ESSENTIAL BASIS OF THE BARGAIN BETWEEN YOU AND CLAYDESK LLC. 
                THE SERVICE WOULD NOT BE PROVIDED WITHOUT THESE LIMITATIONS.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Liability Regardless of Theory</h4>
              <p className="text-sm">
                THE ABOVE LIMITATIONS APPLY REGARDLESS OF THE THEORY OF LIABILITY, WHETHER BASED ON:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>CONTRACT, TORT (INCLUDING NEGLIGENCE), STRICT LIABILITY, OR ANY OTHER LEGAL THEORY</li>
                <li>WHETHER OR NOT CLAYDESK LLC HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES</li>
                <li>WHETHER THE LIMITED REMEDIES PROVIDED HEREIN FAIL OF THEIR ESSENTIAL PURPOSE</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Force Majeure</h4>
              <p className="text-sm">
                CLAYDESK LLC SHALL NOT BE LIABLE FOR ANY DELAY OR FAILURE TO PERFORM DUE TO:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>ACTS OF GOD, NATURAL DISASTERS, OR EXTREME WEATHER</li>
                <li>WAR, TERRORISM, CIVIL UNREST, OR GOVERNMENT ACTIONS</li>
                <li>POWER OUTAGES, INTERNET FAILURES, OR INFRASTRUCTURE PROBLEMS</li>
                <li>THIRD-PARTY SERVICE OUTAGES OR FAILURES (INCLUDING AWS)</li>
                <li>PANDEMICS, EPIDEMICS, OR PUBLIC HEALTH EMERGENCIES</li>
                <li>ANY OTHER CIRCUMSTANCES BEYOND OUR REASONABLE CONTROL</li>
              </ul>
            </div>
            
            <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg">
              <p className="text-amber-800 dark:text-amber-200 text-sm font-semibold mb-2">
                JURISDICTIONAL LIMITATIONS
              </p>
              <p className="text-amber-700 dark:text-amber-300 text-sm">
                SOME JURISDICTIONS DO NOT ALLOW THE LIMITATION OR EXCLUSION OF CERTAIN DAMAGES. 
                IN SUCH JURISDICTIONS, THE ABOVE LIMITATIONS SHALL APPLY TO THE MAXIMUM EXTENT PERMITTED BY LAW.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 13: Indemnification */}
        <Card className="mb-8" id="indemnification">
          <CardHeader>
            <CardTitle>13. Indemnification</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-blue-800 dark:text-blue-200 text-sm font-semibold mb-2">
                COMPREHENSIVE INDEMNIFICATION OBLIGATION
              </p>
              <p className="text-blue-700 dark:text-blue-300 text-sm">
                YOU AGREE TO DEFEND, INDEMNIFY, AND HOLD HARMLESS CLAYDESK LLC AND ALL RELATED PARTIES 
                FROM ANY AND ALL CLAIMS, DAMAGES, LOSSES, AND EXPENSES.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Complete Indemnification</h4>
              <p className="text-sm">
                YOU AGREE TO INDEMNIFY, DEFEND, AND HOLD HARMLESS CLAYDESK LLC, ITS PARENT COMPANIES, 
                SUBSIDIARIES, AFFILIATES, OFFICERS, DIRECTORS, EMPLOYEES, AGENTS, CONTRACTORS, 
                LICENSORS, SERVICE PROVIDERS, SUBCONTRACTORS, SUPPLIERS, AND SUCCESSORS FROM AND AGAINST:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>ANY AND ALL CLAIMS, DEMANDS, LAWSUITS, OR LEGAL PROCEEDINGS</li>
                <li>ALL DAMAGES, LOSSES, COSTS, AND EXPENSES (INCLUDING ATTORNEY'S FEES)</li>
                <li>ALL JUDGMENTS, SETTLEMENTS, AND AWARDS</li>
                <li>ALL LIABILITIES AND OBLIGATIONS OF ANY KIND</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Indemnification Triggers</h4>
              <p className="text-sm">YOUR INDEMNIFICATION OBLIGATION APPLIES TO CLAIMS ARISING FROM OR RELATING TO:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>YOUR USE OF THE SERVICE IN ANY MANNER</li>
                <li>YOUR VIOLATION OF THESE TERMS OR ANY APPLICABLE LAWS</li>
                <li>YOUR USER CONTENT, INCLUDING ALL DATA, CODE, AND MATERIALS YOU PROVIDE</li>
                <li>YOUR VIOLATION OF ANY RIGHTS OF ANOTHER PARTY</li>
                <li>YOUR BREACH OF ANY REPRESENTATIONS OR WARRANTIES</li>
                <li>YOUR NEGLIGENT, RECKLESS, OR INTENTIONAL ACTS OR OMISSIONS</li>
                <li>YOUR INFRINGEMENT OF INTELLECTUAL PROPERTY RIGHTS</li>
                <li>YOUR VIOLATION OF PRIVACY OR PUBLICITY RIGHTS</li>
                <li>YOUR DEFAMATORY, LIBELOUS, OR SLANDEROUS STATEMENTS</li>
                <li>YOUR DEPLOYMENT OF ILLEGAL, HARMFUL, OR OFFENSIVE CONTENT</li>
                <li>YOUR MISUSE OF THIRD-PARTY SERVICES (INCLUDING AWS)</li>
                <li>YOUR FAILURE TO COMPLY WITH SECURITY REQUIREMENTS</li>
                <li>YOUR UNAUTHORIZED DISCLOSURE OF CONFIDENTIAL INFORMATION</li>
                <li>YOUR VIOLATION OF EXPORT CONTROL OR TRADE SANCTION LAWS</li>
                <li>ANY CLAIMS BY YOUR EMPLOYEES, CONTRACTORS, OR AGENTS</li>
                <li>ANY CLAIMS RELATED TO YOUR BUSINESS OPERATIONS</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Defense Obligation</h4>
              <p className="text-sm">
                YOU AGREE TO ASSUME THE DEFENSE OF ANY SUCH CLAIMS AT YOUR OWN EXPENSE, INCLUDING:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>RETAINING QUALIFIED LEGAL COUNSEL ACCEPTABLE TO CLAYDESK LLC</li>
                <li>PAYING ALL LEGAL FEES, COURT COSTS, AND LITIGATION EXPENSES</li>
                <li>COOPERATING FULLY WITH CLAYDESK LLC IN THE DEFENSE</li>
                <li>NOT SETTLING ANY CLAIM WITHOUT CLAYDESK LLC'S WRITTEN CONSENT</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Third-Party Claims</h4>
              <p className="text-sm">
                YOUR INDEMNIFICATION INCLUDES ALL THIRD-PARTY CLAIMS, INCLUDING BUT NOT LIMITED TO:
              </p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>INTELLECTUAL PROPERTY INFRINGEMENT CLAIMS</li>
                <li>PRIVACY AND DATA PROTECTION VIOLATIONS</li>
                <li>DEFAMATION AND BUSINESS DISPARAGEMENT</li>
                <li>EMPLOYMENT AND DISCRIMINATION CLAIMS</li>
                <li>REGULATORY AND COMPLIANCE VIOLATIONS</li>
                <li>PERSONAL INJURY AND PROPERTY DAMAGE</li>
                <li>CONSUMER PROTECTION VIOLATIONS</li>
                <li>ENVIRONMENTAL CLAIMS</li>
                <li>TAX LIABILITIES AND OBLIGATIONS</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Notification and Cooperation</h4>
              <p className="text-sm">
                CLAYDESK LLC WILL PROMPTLY NOTIFY YOU OF ANY CLAIM SUBJECT TO INDEMNIFICATION. 
                YOU AGREE TO COOPERATE FULLY IN THE DEFENSE AND TO PROVIDE ALL NECESSARY INFORMATION AND ASSISTANCE.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Survival</h4>
              <p className="text-sm">
                THIS INDEMNIFICATION OBLIGATION SHALL SURVIVE THE TERMINATION OR EXPIRATION OF THESE TERMS 
                AND YOUR USE OF THE SERVICE, AND SHALL CONTINUE INDEFINITELY.
              </p>
            </div>
            
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
              <p className="text-green-800 dark:text-green-200 text-sm font-semibold mb-2">
                ADDITIONAL PROTECTION
              </p>
              <p className="text-green-700 dark:text-green-300 text-sm">
                IF ANY JURISDICTION LIMITS INDEMNIFICATION, YOU AGREE TO PROVIDE THE MAXIMUM 
                INDEMNIFICATION PERMITTED BY LAW AND TO ADDITIONALLY REIMBURSE CLAYDESK LLC 
                FOR ANY AMOUNTS NOT COVERED BY INDEMNIFICATION.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 14: Complete Disclaimer of Responsibility */}
        <Card className="mb-8" id="no-responsibility">
          <CardHeader>
            <CardTitle className="flex items-center">
              <AlertTriangle className="h-5 w-5 mr-2" />
              14. Complete Disclaimer of Responsibility
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="bg-red-50 dark:bg-red-900/20 p-4 rounded-lg">
              <p className="text-red-800 dark:text-red-200 text-sm font-semibold mb-2">
                CLAYDESK LLC ACCEPTS NO RESPONSIBILITY WHATSOEVER
              </p>
              <p className="text-red-700 dark:text-red-300 text-sm">
                CLAYDESK LLC EXPRESSLY DISCLAIMS AND ASSUMES NO RESPONSIBILITY, LIABILITY, OR OBLIGATION 
                FOR ANY ASPECT OF YOUR USE OF THE SERVICE OR ANY CONSEQUENCES THEREOF.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Responsibility for Service Performance</h4>
              <p className="text-sm">CLAYDESK LLC IS NOT RESPONSIBLE FOR:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>WHETHER THE SERVICE WORKS OR PERFORMS AS EXPECTED</li>
                <li>WHETHER YOUR DEPLOYMENTS ARE SUCCESSFUL OR FAIL</li>
                <li>WHETHER YOUR APPLICATIONS FUNCTION CORRECTLY AFTER DEPLOYMENT</li>
                <li>ANY DOWNTIME, OUTAGES, OR SERVICE INTERRUPTIONS</li>
                <li>THE SPEED, PERFORMANCE, OR RELIABILITY OF THE SERVICE</li>
                <li>ANY ERRORS, BUGS, OR TECHNICAL ISSUES</li>
                <li>COMPATIBILITY WITH YOUR SYSTEMS OR REQUIREMENTS</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Responsibility for Your Content and Data</h4>
              <p className="text-sm">CLAYDESK LLC IS NOT RESPONSIBLE FOR:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>THE ACCURACY, LEGALITY, OR APPROPRIATENESS OF YOUR CONTENT</li>
                <li>ANY LOSS, CORRUPTION, OR UNAUTHORIZED ACCESS TO YOUR DATA</li>
                <li>ANY BACKUP OR RECOVERY OF YOUR DATA</li>
                <li>THE SECURITY OF YOUR CONTENT OR CREDENTIALS</li>
                <li>ANY INTELLECTUAL PROPERTY INFRINGEMENT BY YOUR CONTENT</li>
                <li>COMPLIANCE OF YOUR CONTENT WITH APPLICABLE LAWS</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Responsibility for Third-Party Services</h4>
              <p className="text-sm">CLAYDESK LLC IS NOT RESPONSIBLE FOR:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>ANY AWS SERVICES, COSTS, CHARGES, OR BILLING ISSUES</li>
                <li>ANY GITHUB, GITLAB, OR OTHER VERSION CONTROL ISSUES</li>
                <li>ANY THIRD-PARTY INTEGRATIONS OR DEPENDENCIES</li>
                <li>ANY CHANGES TO THIRD-PARTY TERMS OR PRICING</li>
                <li>ANY THIRD-PARTY SERVICE OUTAGES OR FAILURES</li>
                <li>ANY THIRD-PARTY SECURITY BREACHES OR DATA LOSSES</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Responsibility for Business Impact</h4>
              <p className="text-sm">CLAYDESK LLC IS NOT RESPONSIBLE FOR:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>ANY BUSINESS LOSSES, REVENUE IMPACT, OR OPPORTUNITY COSTS</li>
                <li>ANY DAMAGE TO YOUR REPUTATION OR CUSTOMER RELATIONSHIPS</li>
                <li>ANY REGULATORY OR COMPLIANCE VIOLATIONS</li>
                <li>ANY LEGAL ISSUES ARISING FROM YOUR USE OF THE SERVICE</li>
                <li>ANY EMPLOYMENT OR CONTRACTOR DISPUTES</li>
                <li>ANY TAX IMPLICATIONS OR OBLIGATIONS</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">No Responsibility for Security</h4>
              <p className="text-sm">CLAYDESK LLC IS NOT RESPONSIBLE FOR:</p>
              <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                <li>THE SECURITY OF YOUR ACCOUNTS OR CREDENTIALS</li>
                <li>ANY UNAUTHORIZED ACCESS TO YOUR SYSTEMS</li>
                <li>ANY MALWARE, VIRUSES, OR SECURITY THREATS</li>
                <li>ANY DATA BREACHES OR PRIVACY VIOLATIONS</li>
                <li>YOUR COMPLIANCE WITH SECURITY BEST PRACTICES</li>
                <li>ANY VULNERABILITIES IN YOUR DEPLOYED APPLICATIONS</li>
              </ul>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Use Entirely at Your Own Risk</h4>
              <p className="text-sm">
                YOU ACKNOWLEDGE AND AGREE THAT YOU USE THE SERVICE ENTIRELY AT YOUR OWN RISK. 
                CLAYDESK LLC PROVIDES THE SERVICE ON AN "AS IS" BASIS WITHOUT ANY REPRESENTATION, 
                WARRANTY, OR GUARANTEE OF ANY KIND.
              </p>
            </div>
            
            <div className="bg-orange-50 dark:bg-orange-900/20 p-4 rounded-lg">
              <p className="text-orange-800 dark:text-orange-200 text-sm font-semibold mb-2">
                YOUR SOLE RESPONSIBILITY
              </p>
              <p className="text-orange-700 dark:text-orange-300 text-sm">
                YOU ARE SOLELY AND EXCLUSIVELY RESPONSIBLE FOR ALL ASPECTS OF YOUR USE OF THE SERVICE, 
                INCLUDING ALL CONTENT, DATA, DECISIONS, AND CONSEQUENCES. CLAYDESK LLC ASSUMES NO 
                RESPONSIBILITY WHATSOEVER FOR YOUR ACTIONS OR THEIR RESULTS.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 15: Third-Party Services */}
        <Card className="mb-8" id="third-party">
          <CardHeader>
            <CardTitle>15. Third-Party Services</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm">
              The Service integrates with various third-party services and platforms, including but not limited to:
            </p>
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2">Cloud Providers</h4>
                <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                  <li>Amazon Web Services (AWS)</li>
                  <li>AWS S3, CloudFront, Amplify</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Version Control</h4>
                <ul className="list-disc list-inside space-y-1 ml-4 text-sm">
                  <li>GitHub</li>
                  <li>GitLab</li>
                  <li>Bitbucket</li>
                </ul>
              </div>
            </div>
            <p className="text-sm">
              Your use of third-party services is subject to their respective terms of service and privacy policies. 
              We are not responsible for third-party services or their availability.
            </p>
          </CardContent>
        </Card>

        {/* Section 16: Governing Law */}
        <Card className="mb-8" id="governing-law">
          <CardHeader>
            <CardTitle>16. Governing Law</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm">
              These Terms shall be governed by and construed in accordance with the laws of the State of Connecticut, 
              United States, without regard to its conflict of law provisions.
            </p>
            <p className="text-sm">
              Our failure to enforce any right or provision of these Terms will not be considered a waiver of those rights.
            </p>
          </CardContent>
        </Card>

        {/* Section 17: Dispute Resolution */}
        <Card className="mb-8" id="dispute-resolution">
          <CardHeader>
            <CardTitle>17. Dispute Resolution</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Informal Resolution</h4>
              <p className="text-sm">
                Before filing any formal dispute, you agree to contact us at legal@claydesk.com 
                to seek an informal resolution.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Binding Arbitration</h4>
              <p className="text-sm">
                Any disputes arising from these Terms shall be resolved through binding arbitration 
                in accordance with the Commercial Arbitration Rules of the American Arbitration Association.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Class Action Waiver</h4>
              <p className="text-sm">
                You agree to resolve disputes on an individual basis and waive the right to participate 
                in class action lawsuits or class-wide arbitration.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Jurisdiction</h4>
              <p className="text-sm">
                Any legal action that cannot be resolved through arbitration shall be brought exclusively 
                in the courts of Connecticut, United States.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 18: Changes to Terms */}
        <Card className="mb-8" id="changes">
          <CardHeader>
            <CardTitle>18. Changes to Terms</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm">
              We reserve the right to modify or replace these Terms at any time. If a revision is material, 
              we will provide at least 30 days' notice prior to any new terms taking effect.
            </p>
            <p className="text-sm">
              By continuing to access or use our Service after revisions become effective, 
              you agree to be bound by the revised terms.
            </p>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                <strong>Notification:</strong> We will notify you of material changes via email or through 
                a prominent notice on our Service.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 19: Contact Information */}
        <Card className="mb-8" id="contact">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Mail className="h-5 w-5 mr-2" />
              19. Contact Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm">
              If you have any questions about these Terms of Service, please contact us:
            </p>
            
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">General Inquiries</h4>
                <div className="space-y-1 text-sm">
                  <p>📧 Email: support@claydesk.com</p>
                  <p>🌐 Website: codeflowops.com</p>
                </div>
              </div>
              
              <div>
                <h4 className="font-semibold mb-2">Legal Matters</h4>
                <div className="space-y-1 text-sm">
                  <p>⚖️ Email: legal@claydesk.com</p>
                  <p>📋 DMCA: dmca@claydesk.com</p>
                </div>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Mailing Address</h4>
              <div className="flex items-start">
                <MapPin className="h-4 w-4 mr-2 mt-1 flex-shrink-0" />
                <div className="text-sm">
                  ClayDesk LLC<br />
                  45 Burgundy Hills Lane<br />
                  Middletown, CT 06457<br />
                  United States
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Miscellaneous */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>20. Miscellaneous</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Severability</h4>
              <p className="text-sm">
                If any provision of these Terms is found to be unenforceable, the remaining provisions will remain in full force and effect.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Entire Agreement</h4>
              <p className="text-sm">
                These Terms, together with our Privacy Policy and any other legal notices published by us on the Service, 
                constitute the entire agreement between you and ClayDesk LLC.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Assignment</h4>
              <p className="text-sm">
                You may not assign or transfer these Terms without our written consent. 
                We may assign these Terms without restriction.
              </p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Survival</h4>
              <p className="text-sm">
                Provisions that by their nature should survive termination will survive, including ownership provisions, 
                warranty disclaimers, indemnity, and limitations of liability.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            These Terms of Service are effective as of August 21, 2025.
          </p>
          <p className="mt-2">
            Related documents: <a href="/privacy" className="text-blue-600 hover:underline">Privacy Policy</a> • 
            <a href="/cookies" className="text-blue-600 hover:underline ml-1">Cookie Policy</a>
          </p>
          <p className="mt-4 font-semibold">
            For questions about these Terms, contact legal@claydesk.com
          </p>
        </div>
      </div>
    </div>
  )
}
