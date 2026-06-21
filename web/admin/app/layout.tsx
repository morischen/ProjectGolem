import type { ReactNode } from "react";

export const metadata = {
  title: "EIP Admin — Verdict Browser",
  description:
    "Internal admin portal for reviewing claim verdicts (read-only).",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
