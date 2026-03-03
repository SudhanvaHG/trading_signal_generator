'use client';
import { Activity, RefreshCw } from 'lucide-react';
import { useStore } from '@/store/useStore';
import { Button } from '@/components/ui/Button';
import { triggerManualScan } from '@/lib/api';
import toast from 'react-hot-toast';
import { useState } from 'react';
import { format } from 'date-fns';

interface HeaderProps {
  title: string;
  subtitle?: string;
}

export function Header({ title, subtitle }: HeaderProps) {
  const { isScanning, scanStatus } = useStore();
  const [triggering, setTriggering] = useState(false);

  const handleManualScan = async () => {
    setTriggering(true);
    try {
      const r = await triggerManualScan();
      toast.success(`Scan triggered — ${r.signals_found} signals found`);
    } catch {
      toast.error('Scan failed');
    } finally {
      setTriggering(false);
    }
  };

  const nextRun = scanStatus?.next_run
    ? format(new Date(scanStatus.next_run), 'HH:mm:ss')
    : '—';

  return (
    <header className="h-14 border-b border-bg-border bg-bg-secondary/80 backdrop-blur flex items-center justify-between px-6 sticky top-0 z-20">
      <div>
        <h1 className="text-text-primary font-semibold text-base leading-none">{title}</h1>
        {subtitle && <p className="text-text-secondary text-xs mt-0.5">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-4">
        {/* Scanner status */}
        <div className="hidden sm:flex items-center gap-2 text-xs text-text-secondary font-mono">
          <Activity className="w-3.5 h-3.5 text-accent-green" />
          <span>Scan #{scanStatus?.scan_count ?? 0}</span>
          {scanStatus?.next_run && <span className="text-text-muted">· next {nextRun}</span>}
        </div>

        {/* Manual scan button */}
        <Button
          size="sm"
          variant="secondary"
          icon={<RefreshCw className={`w-3.5 h-3.5 ${isScanning || triggering ? 'animate-spin' : ''}`} />}
          onClick={handleManualScan}
          loading={triggering}
        >
          Scan Now
        </Button>
      </div>
    </header>
  );
}
