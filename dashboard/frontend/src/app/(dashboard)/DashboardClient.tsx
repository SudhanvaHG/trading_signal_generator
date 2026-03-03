'use client';
import { useEffect, useState } from 'react';
import { Header } from '@/components/dashboard/Header';
import { StatCard } from '@/components/ui/StatCard';
import { Card, CardHeader } from '@/components/ui/Card';
import { SignalTable } from '@/components/dashboard/SignalTable';
import { EquityCurveChart } from '@/components/charts/EquityCurveChart';
import { AssetPieChart, StrategyBarChart } from '@/components/charts/StrategyBreakdownChart';
import { useStore } from '@/store/useStore';
import {
  fetchLatestSignals, fetchScanStatus, fetchAllSettings,
  fetchBacktestResult, fetchSignalSummary,
} from '@/lib/api';
import {
  TrendingUp, TrendingDown, Target, Shield,
  BarChart2, Activity, Zap,
} from 'lucide-react';
import { Badge } from '@/components/ui/Badge';

export default function DashboardClient() {
  const {
    signals, setSignals, setScanStatus, setSettings,
    setBacktestResult, backtestResult, liveSignals,
    isScanning, scanSummary,
  } = useStore();

  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const [sigData, scanData, settingsData, sumData] = await Promise.all([
          fetchLatestSignals({ limit: 50 }),
          fetchScanStatus(),
          fetchAllSettings(),
          fetchSignalSummary(),
        ]);
        setSignals(sigData.signals || []);
        setScanStatus(scanData);
        setSettings(settingsData);
        setSummary(sumData);

        // Try loading last backtest if available
        try {
          const bt = await fetchBacktestResult();
          setBacktestResult(bt);
        } catch {}
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    load();
    const interval = setInterval(() => {
      fetchSignalSummary().then(setSummary).catch(() => {});
      fetchScanStatus().then(setScanStatus).catch(() => {});
    }, 30000);
    return () => clearInterval(interval);
  }, []);

  const displaySignals = [...liveSignals, ...signals].slice(0, 50);
  const buyCount = displaySignals.filter(s => s.signal === 'BUY').length;
  const sellCount = displaySignals.filter(s => s.signal === 'SELL').length;
  const avgConf = displaySignals.length
    ? (displaySignals.reduce((a, s) => a + s.confidence, 0) / displaySignals.length * 100).toFixed(0)
    : 0;

  return (
    <div className="animate-fade-in">
      <Header title="Dashboard" subtitle="Live trading signals & performance overview" />

      <div className="p-6 space-y-6">
        {/* Top KPI Row */}
        <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-6 gap-4">
          <StatCard
            title="Total Signals"
            value={summary?.total_signals ?? displaySignals.length}
            sub="this scan"
            color="blue"
            icon={<Zap className="w-4 h-4" />}
          />
          <StatCard
            title="BUY Signals"
            value={summary?.by_type?.BUY ?? buyCount}
            color="green"
            icon={<TrendingUp className="w-4 h-4" />}
          />
          <StatCard
            title="SELL Signals"
            value={summary?.by_type?.SELL ?? sellCount}
            color="red"
            icon={<TrendingDown className="w-4 h-4" />}
          />
          <StatCard
            title="Avg Confidence"
            value={`${avgConf}%`}
            color={Number(avgConf) >= 70 ? 'green' : 'yellow'}
            icon={<Target className="w-4 h-4" />}
          />
          {backtestResult && (
            <>
              <StatCard
                title="Last Backtest"
                value={`${backtestResult.total_return_pct > 0 ? '+' : ''}${backtestResult.total_return_pct?.toFixed(2)}%`}
                sub={`${backtestResult.win_rate_pct?.toFixed(1)}% win rate`}
                color={backtestResult.total_return_pct >= 0 ? 'green' : 'red'}
                trend={backtestResult.total_return_pct >= 0 ? 'up' : 'down'}
                icon={<BarChart2 className="w-4 h-4" />}
              />
              <StatCard
                title="Max Drawdown"
                value={`${backtestResult.max_drawdown_pct?.toFixed(2)}%`}
                sub={backtestResult.challenge_passed ? 'Challenge Passed ✓' : 'In Progress'}
                color={backtestResult.max_drawdown_pct < 5 ? 'green' : backtestResult.max_drawdown_pct < 8 ? 'yellow' : 'red'}
                icon={<Shield className="w-4 h-4" />}
              />
            </>
          )}
        </div>

        {/* Main Grid */}
        <div className="grid grid-cols-1 xl:grid-cols-3 gap-6">
          {/* Signal Table — 2/3 width */}
          <div className="xl:col-span-2">
            <Card>
              <CardHeader
                title="Latest Signals"
                subtitle={`${displaySignals.length} approved signals`}
                action={
                  isScanning
                    ? <Badge variant="yellow" dot>Scanning</Badge>
                    : <Badge variant="green" dot>Live</Badge>
                }
              />
              <SignalTable signals={displaySignals} />
            </Card>
          </div>

          {/* Right column */}
          <div className="space-y-4">
            {/* By Asset */}
            <Card>
              <CardHeader title="Signals by Asset" />
              {summary?.by_asset ? (
                <div className="space-y-2">
                  {Object.entries(summary.by_asset).map(([sym, cnt]: [string, any]) => (
                    <div key={sym} className="flex items-center justify-between text-sm">
                      <span className="font-mono text-text-primary">{sym}</span>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-1.5 bg-bg-border rounded-full overflow-hidden">
                          <div
                            className="h-full bg-accent-blue rounded-full"
                            style={{ width: `${(cnt / (summary.total_signals || 1)) * 100}%` }}
                          />
                        </div>
                        <span className="text-text-secondary text-xs font-mono w-4 text-right">{cnt}</span>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-text-secondary text-xs">Run a scan to see breakdown</p>
              )}
            </Card>

            {/* By Strategy */}
            <Card>
              <CardHeader title="By Strategy" />
              {summary?.by_strategy ? (
                <div className="space-y-2">
                  {Object.entries(summary.by_strategy).map(([strat, cnt]: [string, any]) => {
                    const label = strat.replace('_', ' ');
                    return (
                      <div key={strat} className="flex items-center justify-between text-sm">
                        <span className="text-text-secondary text-xs truncate max-w-[140px]">{label}</span>
                        <Badge variant="blue">{cnt}</Badge>
                      </div>
                    );
                  })}
                </div>
              ) : (
                <p className="text-text-secondary text-xs">No data yet</p>
              )}
            </Card>

            {/* Risk Rules */}
            <Card>
              <CardHeader title="Risk Rules" subtitle="Active constraints" />
              <div className="space-y-1.5 text-xs font-mono">
                {[
                  ['Risk / Trade', '0.5%'],
                  ['Max Trades/Day', '2'],
                  ['Daily Loss Cap', '2%'],
                  ['Max Drawdown', '8%'],
                  ['Min R:R', '1:2'],
                  ['Challenge Target', '10%'],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between">
                    <span className="text-text-secondary">{label}</span>
                    <span className="text-accent-green font-semibold">{val}</span>
                  </div>
                ))}
              </div>
            </Card>
          </div>
        </div>

        {/* Equity Curve (if backtest run) */}
        {backtestResult && (backtestResult.equity_curve?.length ?? 0) > 0 && (
          <Card>
            <CardHeader
              title="Equity Curve"
              subtitle={`Last backtest — ${backtestResult.period} ${backtestResult.timeframe}`}
              action={
                backtestResult.challenge_passed
                  ? <Badge variant="green">Challenge Passed ✓</Badge>
                  : <Badge variant="yellow">In Progress</Badge>
              }
            />
            <EquityCurveChart
              data={backtestResult.equity_curve}
              initialBalance={backtestResult.initial_balance}
            />
          </Card>
        )}
      </div>
    </div>
  );
}
