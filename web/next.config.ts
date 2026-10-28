import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  /* config options here */
  cacheComponents: true,
  partialPrefetching: true,
  // dev.sh points each concurrent dev server at its own dist dir: next dev
  // holds a lock inside distDir, so two servers sharing .next refuse to run.
  distDir: process.env.NEXT_DIST_DIR ?? ".next",
};

export default nextConfig;
