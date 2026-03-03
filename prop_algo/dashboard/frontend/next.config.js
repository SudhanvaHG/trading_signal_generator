/** @type {import('next').NextConfig} */
const BACKEND = process.env.NEXT_PUBLIC_API_URL || 'http://backend:8000';

const nextConfig = {
  output: 'standalone',
  // Allow images from any host (for future asset charts)
  images: { unoptimized: true },
  async rewrites() {
    return [
      // REST API proxy
      { source: '/api/:path*', destination: `${BACKEND}/api/:path*` },
    ];
  },
  // WebSocket is proxied at the Nginx level; no Next.js proxy needed.
  // NEXT_PUBLIC_WS_URL is set by docker-compose for the browser to use directly.
};

module.exports = nextConfig;
