import { RegisterForm } from '@/components/auth/register-form'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign Up | CodeFlowOps',
  description: 'Create your CodeFlowOps account',
}

// Force dynamic rendering for auth pages
export const dynamic = 'force-dynamic'

export default function RegisterPage() {
  return <RegisterForm />
}
