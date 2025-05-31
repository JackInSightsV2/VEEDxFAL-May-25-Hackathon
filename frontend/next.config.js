/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { unoptimized: true },
  // Add webpack configuration to handle cache issues
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.cache = {
        type: 'memory'
      }
    }
    return config
  },
};

module.exports = nextConfig;