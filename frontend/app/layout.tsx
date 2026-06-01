import type { Metadata } from 'next';
import './globals.css';

export const metadata: Metadata = {
  title: 'EFFIONG AI — Sovereign Intelligence Portal',
  description: 'Sovereign Multi-Neural African Intelligence System',
  icons: { icon: '/favicon.ico' },
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-gray-950 text-white">{children}</body>
    </html>
  );
}
