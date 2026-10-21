import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  async rewrites() {
    // Tarayıcıdan /api/* istekleri FastAPI'ye yönlendirilir (CORS gerekmez)
    const api = process.env.API_URL ?? "http://localhost:8000";
    return [{ source: "/api/:path*", destination: `${api}/:path*` }];
  },
};

export default nextConfig;
