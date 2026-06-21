/** @type {import('next').NextConfig} */
const nextConfig = {
  // Transpile the workspace contracts package (TS source, not pre-built).
  transpilePackages: ["@eip/contracts"],
};

export default nextConfig;
