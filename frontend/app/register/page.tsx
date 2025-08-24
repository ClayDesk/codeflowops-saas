import { RegisterForm } from '@/components/auth/register-form'
import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Sign Up | CodeFlowOps',
  description: 'Create your CodeFlowOps account',
}

export default function RegisterPage() {
  return <RegisterForm />
}
