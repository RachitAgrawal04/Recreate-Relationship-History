import type { Metadata } from 'next';
import './globals.css';
import Shell from '@/components/layout/Shell';

export const metadata: Metadata = {
  title: 'Rachit × Radhika — A Private Archive',
  description: 'A personal archive of conversations, May – November 2026.',
  robots: 'noindex, nofollow',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="hi-Latn" className="h-full">
      <head>
        {/* Google Fonts — loaded via <link> so the build doesn't require network */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,300..700;1,8..60,300..700&family=Inter:wght@300..700&family=Noto+Sans+Devanagari:wght@300..700&family=JetBrains+Mono:wght@400&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full antialiased">
        <Shell>{children}</Shell>
      </body>
    </html>
  );
}
