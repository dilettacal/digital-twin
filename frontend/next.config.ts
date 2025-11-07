import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // leaving output undefined so that middleware and Clerk auth can run on the edge runtime
  images: {
    unoptimized: true
  }
};

export default nextConfig;