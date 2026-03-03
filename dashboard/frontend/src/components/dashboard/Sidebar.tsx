'use client';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { clsx } from 'clsx';
import {
  LayoutDashboard, Radio, FlaskConical, Bell,
  Settings, Activity, Zap,
} from 'lucide-react';
import { useStore } from '@/store/useStore';

const NAV = [
  { href: '/',              label: 'Dashboard',    icon: LayoutDashboard },
  { href: '/signals',       label: 'Live Signals', icon: Radio },
  { href: '/backtest',      label: 'Backtest',     icon: FlaskConical },
  { href: '/notifications', label: 'Notifications',icon: Bell },
  { href: '/settings',      label: 'Settings',     icon: Settings },
];

export function Sidebar() {
  const pathname = usePathname();
  const { wsConnected, isScanning, liveSignals } = useStore();

  return (
    <aside className="fixed inset-y-0 left-0 w-56 bg-bg-secondary border-r border-bg-border flex flex-col z-30">
      {/* Logo */}
      <div className="px-5 py-5 border-b border-bg-border">
        <div className="flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-accent-green/10 border border-accent-green/20 flex items-center justify-center">
            <Zap className="w-4 h-4 text-accent-green" />
          </div>
          <div>
            <p className="text-text-primary font-bold text-sm leading-none">PropAlgo</p>
            <p className="text-text-secondary text-[10px] mt-0.5">Trading System</p>
          </div>
        </div>
      </div>

      {/* Status */}
      <div className="px-4 py-3 border-b border-bg-border space-y-1.5">
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-text-secondary uppercase tracking-wider">Live Feed</span>
          <div className="flex items-center gap-1">
            <span className={clsx(
              'w-1.5 h-1.5 rounded-full',
              wsConnected ? 'bg-accent-green animate-pulse' : 'bg-text-muted',
            )} />
            <span className={wsConnected ? 'text-accent-green' : 'text-text-muted'}>
              {wsConnected ? 'Connected' : 'Offline'}
            </span>
          </div>
        </div>
        <div className="flex items-center justify-between text-[10px]">
          <span className="text-text-secondary uppercase tracking-wider">Scanner</span>
          <div className="flex items-center gap-1">
            <span className={clsx(
              'w-1.5 h-1.5 rounded-full',
              isScanning ? 'bg-accent-yellow animate-pulse' : 'bg-accent-green',
            )} />
            <span className={isScanning ? 'text-accent-yellow' : 'text-accent-green'}>
              {isScanning ? 'Scanning...' : 'Active'}
            </span>
          </div>
        </div>
        {liveSignals.length > 0 && (
          <div className="flex items-center justify-between text-[10px]">
            <span className="text-text-secondary uppercase tracking-wider">New Signals</span>
            <span className="bg-accent-green text-bg-primary font-bold rounded px-1.5 py-0.5">
              {liveSignals.length}
            </span>
          </div>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 px-3 py-4 space-y-0.5">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={clsx(
                'flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-all duration-150',
                active
                  ? 'bg-accent-blue/10 text-accent-blue border border-accent-blue/20'
                  : 'text-text-secondary hover:bg-bg-hover hover:text-text-primary',
              )}
            >
              <Icon className="w-4 h-4 flex-shrink-0" />
              {label}
              {href === '/signals' && liveSignals.length > 0 && (
                <span className="ml-auto bg-accent-green text-bg-primary text-[9px] font-bold rounded px-1">
                  {liveSignals.length}
                </span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div className="px-4 py-3 border-t border-bg-border">
        <p className="text-text-muted text-[9px] text-center">PropAlgo v1.0 • Production</p>
      </div>
    </aside>
  );
}
