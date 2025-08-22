import { LoginForm } from '@/components/auth/login-form'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign In | CodeFlowOps',
  description: 'Sign in to your CodeFlowOps account',
}

// Force dynamic rendering for auth pages
export const dynamic = 'force-dynamic'

export default function LoginPage() {
  return <LoginForm />
}
