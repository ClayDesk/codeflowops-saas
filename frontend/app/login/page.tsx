import { LoginForm } from '@/components/auth/login-form'
import { Suspense } from 'react'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign In | CodeFlowOps',
  description: 'Sign in to your CodeFlowOps account',
}

export default function LoginPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <LoginForm />
    </Suspense>
  )
}
