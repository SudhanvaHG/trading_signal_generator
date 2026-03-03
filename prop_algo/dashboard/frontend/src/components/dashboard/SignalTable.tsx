'use client';
import { Badge } from '@/components/ui/Badge';
import { clsx } from 'clsx';
import { Signal } from '@/store/useStore';

interface SignalTableProps {
  signals: Signal[];
  compact?: boolean;
}

function ConfidenceBar({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const color = pct >= 75 ? 'bg-accent-green' : pct >= 55 ? 'bg-accent-yellow' : 'bg-accent-red';
  return (
    <div className="flex items-center gap-2">
      <div className="w-20 h-1.5 bg-bg-border rounded-full overflow-hidden">
        <div className={clsx('h-full rounded-full', color)} style={{ width: `${pct}%` }} />
      </div>
      <span className="text-text-secondary text-[10px] font-mono">{pct}%</span>
    </div>
  );
}

export function SignalTable({ signals, compact }: SignalTableProps) {
  if (!signals.length) {
    return (
      <div className="flex flex-col items-center justify-center py-16 text-text-secondary">
        <p className="text-4xl mb-3">📡</p>
        <p className="text-sm">No signals in this scan.</p>
        <p className="text-xs mt-1">Signals will appear here as they are generated.</p>
      </div>
    );
  }

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-xs font-mono">
        <thead>
          <tr className="border-b border-bg-border text-text-secondary text-[10px] uppercase tracking-wider">
            <th className="text-left py-2 px-3">Date</th>
            <th className="text-left py-2 px-3">Symbol</th>
            <th className="text-left py-2 px-3">Dir</th>
            <th className="text-left py-2 px-3">Strategy</th>
            <th className="text-right py-2 px-3">Entry</th>
            <th className="text-right py-2 px-3">SL</th>
            <th className="text-right py-2 px-3">TP</th>
            <th className="text-right py-2 px-3">R:R</th>
            <th className="text-left py-2 px-3">Confidence</th>
            <th className="text-center py-2 px-3">Vol</th>
          </tr>
        </thead>
        <tbody>
          {signals.map((s, i) => {
            const isBuy = s.signal === 'BUY';
            const date = s.timestamp?.toString().slice(0, 10) || '—';
            return (
              <tr key={i} className="border-b border-bg-border/50 hover:bg-bg-hover/50 transition-colors">
                <td className="py-2 px-3 text-text-secondary">{date}</td>
                <td className="py-2 px-3 font-semibold text-text-primary">{s.symbol}</td>
                <td className="py-2 px-3">
                  <Badge variant={isBuy ? 'green' : 'red'} dot>
                    {s.signal}
                  </Badge>
                </td>
                <td className="py-2 px-3 text-text-secondary">{s.strategy?.replace('_', ' ')}</td>
                <td className="py-2 px-3 text-right text-text-primary">{Number(s.entry).toFixed(4)}</td>
                <td className="py-2 px-3 text-right text-accent-red">{Number(s.stop_loss).toFixed(4)}</td>
                <td className="py-2 px-3 text-right text-accent-green">{Number(s.take_profit).toFixed(4)}</td>
                <td className="py-2 px-3 text-right">
                  <span className={clsx('font-semibold', s.rr_ratio >= 2 ? 'text-accent-green' : 'text-accent-yellow')}>
                    1:{Number(s.rr_ratio).toFixed(1)}
                  </span>
                </td>
                <td className="py-2 px-3"><ConfidenceBar value={s.confidence} /></td>
                <td className="py-2 px-3 text-center">
                  {s.volume_ok
                    ? <span className="text-accent-green">✓</span>
                    : <span className="text-accent-red">✗</span>}
                </td>
              </tr>
            );
          })}
        </tbody>
      </table>
    </div>
  );
}
