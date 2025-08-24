/** @type {import('next').NextConfig} */
const nextConfig = {
  // Disable static export for Amplify deployment - use SSR instead
  // ...(process.env.NODE_ENV === 'production' && process.env.BUILD_MODE === 'export' ? {
  //   output: 'export',
  //   distDir: 'out',
  //   trailingSlash: true,
  // } : {}),
  basePath: '',
  assetPrefix: '',
  images: {
    unoptimized: true,
    domains: ['localhost', 'avatars.githubusercontent.com', 'images.unsplash.com'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000',
  },
  // Multi-tenant subdomain support
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL}/api/:path*`,
      },
    ]
  },
  // Tenant-aware redirects
  async redirects() {
    return [
      {
        source: '/dashboard',
        destination: '/dashboard/overview',
        permanent: false,
      },
    ]
  },
}

module.exports = nextConfig
