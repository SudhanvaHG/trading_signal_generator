'use client';
import { useEffect, useState } from 'react';
import { Header } from '@/components/dashboard/Header';
import { Card, CardHeader } from '@/components/ui/Card';
import { SignalTable } from '@/components/dashboard/SignalTable';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { StatCard } from '@/components/ui/StatCard';
import { useStore } from '@/store/useStore';
import { fetchLatestSignals, fetchScanStatus, setScanInterval } from '@/lib/api';
import { Radio, Filter, Clock } from 'lucide-react';
import toast from 'react-hot-toast';

const ASSETS = ['All', 'XAUUSD', 'BTCUSD', 'XRPUSD', 'EURUSD'];
const STRATEGIES = ['All', 'Breakout_Retest', 'EMA_Trend_Pullback', 'Mean_Reversion'];
const DIRECTIONS = ['All', 'BUY', 'SELL'];

export default function SignalsPage() {
  const { liveSignals, signals, setSignals, setScanStatus, scanStatus, isScanning } = useStore();
  const [filterAsset, setFilterAsset] = useState('All');
  const [filterDir, setFilterDir] = useState('All');
  const [filterStrat, setFilterStrat] = useState('All');
  const [minConf, setMinConf] = useState(0);
  const [newInterval, setNewInterval] = useState(60);
  const [updatingInterval, setUpdatingInterval] = useState(false);

  useEffect(() => {
    Promise.all([fetchLatestSignals({ limit: 200 }), fetchScanStatus()])
      .then(([sig, scan]) => {
        setSignals(sig.signals || []);
        setScanStatus(scan);
        setNewInterval(scan.interval_seconds || 60);
      })
      .catch(console.error);
  }, []);

  const allSignals = [...liveSignals, ...signals];
  let filtered = allSignals;
  if (filterAsset !== 'All') filtered = filtered.filter(s => s.symbol === filterAsset);
  if (filterDir !== 'All')   filtered = filtered.filter(s => s.signal === filterDir);
  if (filterStrat !== 'All') filtered = filtered.filter(s => s.strategy === filterStrat);
  if (minConf > 0)           filtered = filtered.filter(s => s.confidence >= minConf / 100);

  const handleUpdateInterval = async () => {
    setUpdatingInterval(true);
    try {
      await setScanInterval(newInterval);
      toast.success(`Scan interval updated to ${newInterval}s`);
    } catch {
      toast.error('Failed to update interval');
    } finally {
      setUpdatingInterval(false);
    }
  };

  return (
    <div className="animate-fade-in">
      <Header title="Live Signals" subtitle="Real-time signal feed with filters" />

      <div className="p-6 space-y-6">
        {/* Stats */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
          <StatCard title="Total" value={allSignals.length} color="white" />
          <StatCard title="BUY" value={allSignals.filter(s=>s.signal==='BUY').length} color="green" />
          <StatCard title="SELL" value={allSignals.filter(s=>s.signal==='SELL').length} color="red" />
          <StatCard title="Filtered" value={filtered.length} color="blue" />
        </div>

        {/* Scan Control */}
        <Card>
          <CardHeader title="Scanner Control" subtitle="Manage the live scan interval" action={
            isScanning ? <Badge variant="yellow" dot>Scanning</Badge> : <Badge variant="green" dot>Idle</Badge>
          } />
          <div className="flex flex-wrap items-center gap-3">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-text-secondary" />
              <span className="text-text-secondary text-sm">Refresh every</span>
              <input
                type="number"
                value={newInterval}
                onChange={e => setNewInterval(Number(e.target.value))}
                min={30} max={86400}
                className="w-20 bg-bg-border border border-bg-border text-text-primary text-sm rounded-lg px-2 py-1 font-mono"
              />
              <span className="text-text-secondary text-sm">seconds</span>
            </div>
            <Button
              size="sm" variant="primary"
              onClick={handleUpdateInterval}
              loading={updatingInterval}
            >
              Update
            </Button>
            {scanStatus?.next_run && (
              <span className="text-text-secondary text-xs font-mono ml-auto">
                Next scan: {new Date(scanStatus.next_run).toLocaleTimeString()}
              </span>
            )}
          </div>
        </Card>

        {/* Filters */}
        <Card>
          <CardHeader title="Filters" action={<Filter className="w-4 h-4 text-text-secondary" />} />
          <div className="flex flex-wrap gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-text-secondary text-[10px] uppercase tracking-wider">Asset</label>
              <div className="flex gap-1">
                {ASSETS.map(a => (
                  <button key={a} onClick={() => setFilterAsset(a)}
                    className={`px-2.5 py-1 rounded text-xs font-mono border transition-all ${filterAsset===a ? 'bg-accent-blue/10 text-accent-blue border-accent-blue/30' : 'border-bg-border text-text-secondary hover:border-bg-hover'}`}>
                    {a}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-text-secondary text-[10px] uppercase tracking-wider">Direction</label>
              <div className="flex gap-1">
                {DIRECTIONS.map(d => (
                  <button key={d} onClick={() => setFilterDir(d)}
                    className={`px-2.5 py-1 rounded text-xs font-mono border transition-all ${filterDir===d ? 'bg-accent-blue/10 text-accent-blue border-accent-blue/30' : 'border-bg-border text-text-secondary hover:border-bg-hover'}`}>
                    {d}
                  </button>
                ))}
              </div>
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-text-secondary text-[10px] uppercase tracking-wider">Min Confidence</label>
              <div className="flex items-center gap-2">
                <input
                  type="range" min={0} max={100} step={5} value={minConf}
                  onChange={e => setMinConf(Number(e.target.value))}
                  className="w-32 accent-accent-blue"
                />
                <span className="text-xs font-mono text-text-secondary">{minConf}%</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Signal Table */}
        <Card>
          <CardHeader
            title="Signals"
            subtitle={`${filtered.length} signals matching filters`}
            action={
              liveSignals.length > 0 && (
                <Badge variant="green" dot>{liveSignals.length} live</Badge>
              )
            }
          />
          <SignalTable signals={filtered} />
        </Card>
      </div>
    </div>
  );
}
