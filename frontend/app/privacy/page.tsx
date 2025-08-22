'use client'

import React from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { Shield, Mail, MapPin, Calendar, FileText, Users, Lock, Database, Globe, AlertTriangle } from 'lucide-react'

export default function PrivacyPolicyPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-slate-100 dark:from-slate-900 dark:to-slate-800">
      <div className="container mx-auto px-4 py-8 max-w-4xl">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center mb-4">
            <Shield className="h-12 w-12 text-blue-600 mr-3" />
            <h1 className="text-4xl font-bold text-slate-900 dark:text-slate-100">
              Privacy Policy
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

        {/* Document Meta */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <FileText className="h-5 w-5 mr-2" />
              Document Information
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <strong>Legal Entity/Data Controller:</strong>
                <p className="text-slate-600 dark:text-slate-400">ClayDesk LLC</p>
              </div>
              <div>
                <strong>Registered Address:</strong>
                <p className="text-slate-600 dark:text-slate-400">
                  45 Burgundy Hills Lane<br />
                  Middletown, CT 06457, USA
                </p>
              </div>
            </div>
            <div>
              <strong>Coverage:</strong>
              <div className="flex flex-wrap gap-2 mt-2">
                <Badge variant="secondary">CodeFlowOps Web App</Badge>
                <Badge variant="secondary">Platform APIs</Badge>
                <Badge variant="secondary">CLI/VS Code Extension</Badge>
              </div>
            </div>
            <div>
              <strong>Related Documents:</strong>
              <p className="text-slate-600 dark:text-slate-400">
                Terms of Service • Cookie Policy • Security Overview • Subprocessor List • Data Processing Addendum (DPA)
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 1: Who We Are */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Users className="h-5 w-5 mr-2" />
              1. Who We Are & What We Do
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p>
              CodeFlowOps is a deployment automation platform that analyzes and builds/deploys static and React front-end applications.
            </p>
            <p>
              We host the CodeFlowOps platform on AWS and deploy customer front-ends to customer-owned AWS infrastructure 
              (e.g., S3 + CloudFront, AWS Amplify Hosting) when AWS is selected as the deployment destination.
            </p>
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="font-semibold text-blue-800 dark:text-blue-200">Important:</p>
              <p className="text-blue-700 dark:text-blue-300">
                We do not host or operate back-ends or databases. CodeFlowOps focuses exclusively on front-end deployment automation.
              </p>
            </div>
            <div>
              <strong>Parent Company:</strong>
              <p>ClayDesk LLC, 45 Burgundy Hills Lane, Middletown, CT 06457, USA</p>
            </div>
            <div>
              <strong>Privacy Contact:</strong>
              <p className="flex items-center">
                <Mail className="h-4 w-4 mr-2" />
                privacy@claydesk.com
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 2: Roles & Definitions */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>2. Roles & Definitions</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <strong>Data Controller (platform data):</strong>
                <p>ClayDesk LLC for account, billing, and service-operation data.</p>
              </div>
              <div>
                <strong>Processor/Service Provider:</strong>
                <p>We act as a processor for repository/build data processed on your behalf.</p>
              </div>
              <div className="grid md:grid-cols-2 gap-4 mt-6">
                <div className="space-y-3">
                  <div>
                    <Badge variant="outline">"Repository Data"</Badge>
                    <p className="text-sm mt-1">Source code and configuration you connect for builds.</p>
                  </div>
                  <div>
                    <Badge variant="outline">"Build Artifacts"</Badge>
                    <p className="text-sm mt-1">Compiled static assets produced by our build steps.</p>
                  </div>
                  <div>
                    <Badge variant="outline">"Client Config"</Badge>
                    <p className="text-sm mt-1">Public client-side values (e.g., Firebase config, Supabase URL/anon key).</p>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <Badge variant="outline">"Telemetry"</Badge>
                    <p className="text-sm mt-1">Usage and performance data collected to keep the service reliable.</p>
                  </div>
                  <div>
                    <Badge variant="outline">"Subprocessors"</Badge>
                    <p className="text-sm mt-1">Vendors we use (e.g., Amazon Web Services, Inc.).</p>
                  </div>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section 3: Data We Collect */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Database className="h-5 w-5 mr-2" />
              3. Data We Collect
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-6">
            <div>
              <h4 className="font-semibold text-lg mb-3">3.1 Account & Authentication</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Name, email, avatar</li>
                <li>OAuth IDs (GitHub/Google) within granted scopes</li>
                <li>Workspace memberships and roles</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-lg mb-3">3.2 Billing (if applicable)</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Billing contact, plan, invoices</li>
                <li>Payment card data handled by our payment processor (not stored by us)</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-lg mb-3">3.3 Repository & Project Data (front-end only)</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Repo metadata (URL, branches, commit SHAs, languages)</li>
                <li>Files required to build static/React apps (e.g., package.json, src/, public/)</li>
                <li>Environment inputs for front-end builds (client-safe values only, no admin/service secrets)</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-lg mb-3">3.4 Build & Deployment Data</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Build logs (with secret redaction), statuses, durations, sizes/hashes</li>
                <li>Deployment targets: AWS S3 bucket names/ARNs, CloudFront distribution IDs, Amplify app IDs</li>
                <li>CDN cache settings and invalidations; SPA routing/redirect settings</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-lg mb-3">3.5 Optional Client-Side BaaS Config</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Firebase/Firestore public config (apiKey, projectId, etc.)</li>
                <li>Supabase URL and anon/public key</li>
              </ul>
              <div className="bg-amber-50 dark:bg-amber-900/20 p-3 rounded-lg mt-2">
                <p className="text-amber-800 dark:text-amber-200 text-sm">
                  <AlertTriangle className="h-4 w-4 inline mr-1" />
                  We require Firestore Security Rules / Supabase RLS ON before go-live for client-only apps.
                </p>
              </div>
            </div>

            <div>
              <h4 className="font-semibold text-lg mb-3">3.6 Usage, Device & Diagnostic Data</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Interaction telemetry, performance metrics, error reports</li>
                <li>IP, timestamps, user agent, OS/browser</li>
                <li>Cookie identifiers (see Cookie section)</li>
              </ul>
            </div>

            <div>
              <h4 className="font-semibold text-lg mb-3">3.7 AWS-Specific Data We May Handle</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Your selected AWS region(s) for deployment</li>
                <li>AWS account IDs/ARNs you authorize for deployment targets</li>
                <li>Temporary credentials or roles (preferred: assume-role with external ID)</li>
              </ul>
              <p className="text-sm text-slate-500 mt-2">
                Storage is minimized, time-bound, and encrypted at rest when retained.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 4: How We Collect */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>4. How We Collect Data</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="list-disc list-inside space-y-2 text-slate-600 dark:text-slate-400">
              <li>Direct input (connecting repos/cloud, entering client config)</li>
              <li>OAuth (scoped access)</li>
              <li>Automated collection by our app (telemetry, cookies/consent)</li>
            </ul>
          </CardContent>
        </Card>

        {/* Section 5: How We Use Data */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>5. How We Use Data (Purposes)</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">We use your data to:</h4>
              <ul className="list-disc list-inside space-y-1 text-slate-600 dark:text-slate-400">
                <li>Provide/operate the service (analyze, build, deploy static/React apps to your AWS targets)</li>
                <li>Security (abuse prevention, incident response)</li>
                <li>Support/Communications (status, notifications, assistance)</li>
                <li>Product improvement & analytics (aggregate/limited telemetry, consent where required)</li>
                <li>Compliance (legal, accounting, audits)</li>
              </ul>
            </div>
            
            <div className="bg-green-50 dark:bg-green-900/20 p-4 rounded-lg">
              <h4 className="font-semibold text-green-800 dark:text-green-200 mb-2">We do NOT:</h4>
              <ul className="list-disc list-inside space-y-1 text-green-700 dark:text-green-300 text-sm">
                <li>Sell personal data</li>
                <li>Train general-purpose ML models on your proprietary code</li>
                <li>Host your back-end or database infrastructure</li>
                <li>Write admin/service secrets into REACT_APP_* or client bundles</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Section 6: Legal Bases */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>6. Legal Bases (GDPR/UK GDPR)</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div>
                  <Badge>Contract</Badge>
                  <p className="text-sm mt-1">To deliver CodeFlowOps services</p>
                </div>
                <div>
                  <Badge>Legitimate Interests</Badge>
                  <p className="text-sm mt-1">Security, reliability, limited analytics</p>
                </div>
              </div>
              <div className="space-y-3">
                <div>
                  <Badge>Consent</Badge>
                  <p className="text-sm mt-1">Non-essential cookies/marketing</p>
                </div>
                <div>
                  <Badge>Legal Obligation</Badge>
                  <p className="text-sm mt-1">Tax, fraud, compliance</p>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Section 7: Cookies */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>7. Cookies & Similar Technologies</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-3 gap-4">
              <div>
                <Badge variant="secondary">Necessary</Badge>
                <p className="text-sm mt-1">Auth/session management</p>
              </div>
              <div>
                <Badge variant="secondary">Preferences</Badge>
                <p className="text-sm mt-1">UI settings and user preferences</p>
              </div>
              <div>
                <Badge variant="secondary">Analytics</Badge>
                <p className="text-sm mt-1">Optional/consent-based; opt-out available</p>
              </div>
            </div>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              We honor cookie banner/consent and Global Privacy Control (GPC). 
              For detailed information, see our Cookie Policy.
            </p>
          </CardContent>
        </Card>

        {/* Section 8: Sharing & Subprocessors */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Globe className="h-5 w-5 mr-2" />
              8. Sharing & Subprocessors (including AWS)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">Our Subprocessors Include:</h4>
              <div className="space-y-2">
                <div className="flex items-start space-x-2">
                  <Badge variant="outline">AWS</Badge>
                  <p className="text-sm">Amazon Web Services, Inc. — hosting of the CodeFlowOps platform and services such as S3, CloudFront, Amplify Hosting, CloudWatch, IAM/KMS</p>
                </div>
                <div className="flex items-start space-x-2">
                  <Badge variant="outline">OAuth</Badge>
                  <p className="text-sm">GitHub/Google (sign-in, repo access with user-granted scopes)</p>
                </div>
                <div className="flex items-start space-x-2">
                  <Badge variant="outline">Email/Comms</Badge>
                  <p className="text-sm">Email service providers for notifications</p>
                </div>
                <div className="flex items-start space-x-2">
                  <Badge variant="outline">Monitoring</Badge>
                  <p className="text-sm">Error monitoring/observability providers</p>
                </div>
                <div className="flex items-start space-x-2">
                  <Badge variant="outline">Payments</Badge>
                  <p className="text-sm">Payment processors for billing</p>
                </div>
              </div>
            </div>
            
            <div className="bg-blue-50 dark:bg-blue-900/20 p-4 rounded-lg">
              <p className="text-blue-800 dark:text-blue-200 text-sm">
                All subprocessors are bound by Data Processing Agreements (DPAs). See our live Subprocessor List for complete details.
              </p>
            </div>
            
            <div className="bg-amber-50 dark:bg-amber-900/20 p-4 rounded-lg">
              <p className="text-amber-800 dark:text-amber-200 text-sm">
                <strong>Note:</strong> When you deploy to your own AWS account, AWS is your cloud provider (not our subprocessor) 
                for those deployed artifacts; we act as your agent/processor to execute the deployment in that account.
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Section 9: International Data Transfers */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>9. International Data Transfers</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <strong>Platform hosting region(s):</strong>
              <p>Primary: US East (N. Virginia) - us-east-1</p>
            </div>
            <p>
              Cross-border transfers are safeguarded via Standard Contractual Clauses (SCCs)/UK Addendum 
              or adequacy decisions, as applicable.
            </p>
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Contact us to request copies of transfer mechanisms.
            </p>
          </CardContent>
        </Card>

        {/* Section 10: Security */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Lock className="h-5 w-5 mr-2" />
              10. Security (with AWS specifics)
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-6">
              <div>
                <h4 className="font-semibold mb-2">Encryption</h4>
                <ul className="text-sm space-y-1">
                  <li>• In transit: TLS 1.2+</li>
                  <li>• At rest: AWS-managed or KMS encryption</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Access Controls</h4>
                <ul className="text-sm space-y-1">
                  <li>• Least privilege principle</li>
                  <li>• Role-based access</li>
                  <li>• Short-lived tokens</li>
                  <li>• AssumeRole with external IDs preferred</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Secrets Management</h4>
                <ul className="text-sm space-y-1">
                  <li>• Never embed admin/service creds in client builds</li>
                  <li>• Secrets redaction in logs</li>
                  <li>• Build-time validations block disallowed patterns</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">AWS Controls</h4>
                <ul className="text-sm space-y-1">
                  <li>• IAM policies</li>
                  <li>• VPC isolation (where relevant)</li>
                  <li>• CloudWatch logging/alarms</li>
                </ul>
              </div>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">Front-end Hardening</h4>
              <ul className="text-sm space-y-1 text-slate-600 dark:text-slate-400">
                <li>• SPA rewrites (403/404 → index.html)</li>
                <li>• CloudFront invalidation post-deploy</li>
                <li>• Caching policy (index.html no-cache, static assets long TTL + immutable)</li>
                <li>• Auditability: we log the source of client config (repo vs deployment payload)</li>
              </ul>
            </div>
          </CardContent>
        </Card>

        {/* Section 11: Retention & Deletion */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>11. Retention & Deletion</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid md:grid-cols-2 gap-4">
              <div>
                <h4 className="font-semibold mb-2">Short-term Data</h4>
                <ul className="text-sm space-y-1">
                  <li>• Ephemeral clones/build caches: 7–30 days</li>
                  <li>• Build logs/metadata: 30–90 days (sanitized)</li>
                  <li>• Credentials/roles: short-lived, encrypted when retained</li>
                </ul>
              </div>
              <div>
                <h4 className="font-semibold mb-2">Long-term Data</h4>
                <ul className="text-sm space-y-1">
                  <li>• Account/profile/billing: account life + legal periods</li>
                  <li>• Deployed artifacts: reside in your AWS accounts</li>
                  <li>• Your retention policies apply to deployed content</li>
                </ul>
              </div>
            </div>
            
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Self-service deletion available through your account settings. 
              Contact support for full deletion requests. Backup purge windows will be disclosed.
            </p>
          </CardContent>
        </Card>

        {/* Section 12: Your Rights */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>12. Your Rights</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <h4 className="font-semibold mb-2">GDPR/UK GDPR Rights:</h4>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">Access</Badge>
                <Badge variant="outline">Rectification</Badge>
                <Badge variant="outline">Erasure</Badge>
                <Badge variant="outline">Restriction</Badge>
                <Badge variant="outline">Portability</Badge>
                <Badge variant="outline">Objection</Badge>
              </div>
              <p className="text-sm mt-2">Right to complaint to a supervisory authority</p>
            </div>
            
            <div>
              <h4 className="font-semibold mb-2">CCPA/CPRA (California) Rights:</h4>
              <div className="flex flex-wrap gap-2">
                <Badge variant="outline">Know/Access</Badge>
                <Badge variant="outline">Correct</Badge>
                <Badge variant="outline">Delete</Badge>
                <Badge variant="outline">Opt-out</Badge>
              </div>
              <p className="text-sm mt-2">We do not sell personal data. No discrimination for exercising rights.</p>
            </div>
            
            <p className="text-sm text-slate-600 dark:text-slate-400">
              Contact privacy@claydesk.com to exercise your rights. Verification steps and typical timelines will be provided.
            </p>
          </CardContent>
        </Card>

        {/* Section 13: Choices & Controls */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>13. Choices & Controls</CardTitle>
          </CardHeader>
          <CardContent>
            <ul className="space-y-2 text-slate-600 dark:text-slate-400">
              <li>• Cookie/analytics preferences; GPC honored</li>
              <li>• Email preference center</li>
              <li>• Telemetry opt-out (where offered)</li>
              <li>• Revoke OAuth access from provider settings (GitHub/Google)</li>
              <li>• Export/delete data where supported</li>
            </ul>
          </CardContent>
        </Card>

        {/* Section 14: Children's Privacy */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>14. Children's Privacy</CardTitle>
          </CardHeader>
          <CardContent>
            <p>
              CodeFlowOps is not directed to children under 13 (or local equivalent age). 
              We do not knowingly collect personal information from children.
            </p>
          </CardContent>
        </Card>

        {/* Section 15: Third-Party Links & SDKs */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>15. Third-Party Links & SDKs</CardTitle>
          </CardHeader>
          <CardContent>
            <p>
              Links and embedded SDKs/scripts (e.g., OAuth buttons, analytics) are governed by those parties' respective privacy policies.
            </p>
          </CardContent>
        </Card>

        {/* Section 16: Changes to This Policy */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>16. Changes to This Policy</CardTitle>
          </CardHeader>
          <CardContent>
            <p>
              We will notify you of material changes via email or in-app notification. 
              Prior versions of this policy are available upon request.
            </p>
          </CardContent>
        </Card>

        {/* Section 17: Contact Us */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center">
              <Mail className="h-5 w-5 mr-2" />
              17. Contact Us
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <strong>ClayDesk LLC</strong>
              <div className="flex items-start mt-2">
                <MapPin className="h-4 w-4 mr-2 mt-1 flex-shrink-0" />
                <div>
                  45 Burgundy Hills Lane<br />
                  Middletown, CT 06457, USA
                </div>
              </div>
            </div>
            
            <div className="flex items-center">
              <Mail className="h-4 w-4 mr-2" />
              <strong>Privacy Email:</strong>
              <span className="ml-2">privacy@claydesk.com</span>
            </div>
          </CardContent>
        </Card>

        {/* Section 18: US State Privacy Addendum */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>18. US State Privacy Addendum</CardTitle>
          </CardHeader>
          <CardContent>
            <p>
              For residents of Virginia, Colorado, Connecticut, Utah, and other applicable states: 
              Additional rights regarding sensitive data handling and appeal processes are available. 
              Contact us for state-specific information.
            </p>
          </CardContent>
        </Card>

        {/* Section 19: Engineering & Operational Disclosures */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>19. Engineering & Operational Disclosures</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <ul className="space-y-2 text-sm text-slate-600 dark:text-slate-400">
              <li>• Never accept or write admin/service credentials to REACT_APP_* or repo files destined for client bundles</li>
              <li>• Require Firestore Rules/Supabase RLS ON for client-only apps pre-deployment</li>
              <li>• SPA routing set: 403/404 → index.html; CloudFront invalidation after deploy</li>
              <li>• Caching: index.html no-cache; assets long TTL + immutable</li>
              <li>• Provenance logging for client config (repo vs deployment payload)</li>
              <li>• AWS-specific: prefer AssumeRole with external ID; minimize and encrypt any stored credentials; region pinning where feasible</li>
            </ul>
          </CardContent>
        </Card>

        {/* Appendices */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle>Appendices</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid md:grid-cols-2 gap-4 text-sm">
              <div>
                <strong>A. Subprocessor List</strong>
                <p className="text-slate-600 dark:text-slate-400">
                  Includes Amazon Web Services, Inc.: S3, CloudFront, Amplify Hosting, CloudWatch, IAM/KMS; plus other vendors
                </p>
              </div>
              <div>
                <strong>B. Data Retention Schedule</strong>
                <p className="text-slate-600 dark:text-slate-400">
                  Tables per dataset & TTLs
                </p>
              </div>
              <div>
                <strong>C. Telemetry Event Catalog</strong>
                <p className="text-slate-600 dark:text-slate-400">
                  Fields + redaction policies
                </p>
              </div>
              <div>
                <strong>D. Security Overview</strong>
                <p className="text-slate-600 dark:text-slate-400">
                  Controls mapped to common frameworks
                </p>
              </div>
              <div>
                <strong>E. Cookie Table</strong>
                <p className="text-slate-600 dark:text-slate-400">
                  Names, purposes, durations
                </p>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Footer */}
        <div className="text-center text-sm text-slate-500 border-t pt-8">
          <p>
            This privacy policy is effective as of August 21, 2025. 
            For questions about this policy, contact privacy@claydesk.com
          </p>
        </div>
      </div>
    </div>
  )
}
