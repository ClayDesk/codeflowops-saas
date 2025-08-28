import { Metadata } from 'next'
import { Hero } from '@/components/landing/Hero'
import { Features } from '@/components/landing/Features'
import { HowItWorks } from '@/components/landing/HowItWorks'
import { Testimonials } from '@/components/landing/Testimonials'
// import { Navbar } from '@/components/landing/Navbar'
// import { Footer } from '@/components/landing/Footer'

export const metadata: Metadata = {
  title: 'CodeFlowOps - Deploy React & Static Sites to AWS Instantly',
  description: 'Deploy your React apps and static sites from GitHub to AWS S3 + CloudFront in minutes. Simple 5-step workflow: GitHub URL → Live Website.',
  keywords: 'React deployment, AWS, S3, CloudFront, GitHub, CI/CD, static sites, web hosting',
}

export default function HomePage() {
  return (
    <main>
      <Hero />
      <Features />
      <HowItWorks />
      <Testimonials />
    </main>
  )
}
