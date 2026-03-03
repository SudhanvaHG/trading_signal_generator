// Server component wrapper — keeps 'use client' out of the page boundary
// so Next.js standalone build correctly generates the client reference manifest.
import DashboardClient from './DashboardClient';

export default function DashboardPage() {
  return <DashboardClient />;
}
