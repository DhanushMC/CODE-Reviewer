import type { Metadata } from 'next';
import './globals.css';   // BUG FIX: CSS was never imported — no styles were applying

export const metadata: Metadata = {
  title: 'Secure Code Reviewer',
  description: 'Intent-Aware AI-Driven Vulnerability Detection & Correction',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="antialiased">{children}</body>
    </html>
  );
}
