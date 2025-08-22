import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import { Navbar } from '@/components/landing/Navbar'
import { Footer } from '@/components/landing/Footer'
import { Providers } from './providers'

const inter = Inter({
  subsets: ['latin'],
  variable: '--font-sans',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'CodeFlowOps Simple SaaS',
  description: 'Simple 5-step workflow: GitHub URL → Live Website',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className={inter.variable} suppressHydrationWarning>
      <body className="min-h-screen bg-background font-sans antialiased">
        <Providers>
          <Navbar />
          <main className="min-h-[80vh] flex flex-col justify-between">
            {children}
          </main>
          <Footer />
        </Providers>
      </body>
    </html>
  )
}
