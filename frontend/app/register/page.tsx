import { Suspense } from 'react'
import { RegisterForm } from '@/components/auth/register-form'
import type { Metadata } from 'next'
import { Loader2 } from 'lucide-react'

export const metadata: Metadata = {
  title: 'Sign Up | CodeFlowOps',
  description: 'Create your CodeFlowOps account',
}

function RegisterFormFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
      <div className="flex items-center space-x-2">
        <Loader2 className="h-6 w-6 animate-spin" />
        <span>Loading registration form...</span>
      </div>
    </div>
  )
}

export default function RegisterPage() {
  return (
    <Suspense fallback={<RegisterFormFallback />}>
      <RegisterForm />
    </Suspense>
  )
}
