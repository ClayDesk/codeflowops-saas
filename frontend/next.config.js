/** @type {import('next').NextConfig} */
const nextConfig = {
  // Static export for Amplify
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
    domains: ['localhost', 'avatars.githubusercontent.com', 'images.unsplash.com'],
  },
  env: {
    CUSTOM_KEY: process.env.CUSTOM_KEY,
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://api.codeflowops.com',
  },
}

module.exports = nextConfig
