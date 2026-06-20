import type { ReactNode } from "react";

export const metadata = {
  title: "Evidence Intelligence Platform",
  description: "Transparent, evidence-based assessment of disputed claims.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
