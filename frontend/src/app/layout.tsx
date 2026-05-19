import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'DATASHIELD | Enterprise AI Data Governance',
  description: 'AI-powered enterprise data governance platform for banks, government institutions, and regulated industries. Real-time monitoring, classification, and compliance.',
  keywords: ['data governance', 'AI', 'compliance', 'security', 'GDPR', 'ISO 27001'],
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en" dir="ltr" className="dark antialiased" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <meta name="theme-color" content="#020617" />
      </head>
      <body className="min-h-screen bg-surface-950 text-slate-50 font-sans">
        {children}
      </body>
    </html>
  );
}
