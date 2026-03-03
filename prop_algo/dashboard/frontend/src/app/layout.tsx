import type { Metadata } from 'next';
import './globals.css';
import { Toaster } from 'react-hot-toast';
import { WSProvider } from './WSProvider';

export const metadata: Metadata = {
  title: 'PropAlgo — Trading Dashboard',
  description: 'Prop Firm Algorithmic Trading System',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="dark">
      <body className="bg-bg-primary text-text-primary antialiased">
        <WSProvider />
        {children}
        <Toaster position="top-right" />
      </body>
    </html>
  );
}
