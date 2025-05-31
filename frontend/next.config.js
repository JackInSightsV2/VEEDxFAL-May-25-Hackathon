const path = require('path');

/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: { unoptimized: true },
  // Add webpack configuration to handle cache issues and path resolution
  webpack: (config, { dev, isServer }) => {
    if (dev) {
      config.cache = {
        type: 'memory'
      }
    }
    
    // Add path resolution for @ alias
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname),
    };
    
    return config
  },
};

module.exports = nextConfig;