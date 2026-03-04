'use client';
import { useEffect, useRef, useState } from 'react';
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
  runBacktest, fetchBacktestStatus,
} from '@/lib/api';
import {
  TrendingUp, TrendingDown, Target, Shield,
  BarChart2, Activity, Zap, PlayCircle, Loader2,
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
  const [isRunningBacktest, setIsRunningBacktest] = useState(false);
  const [btPeriod, setBtPeriod] = useState('1y');
  const [btStartDate, setBtStartDate] = useState('');
  const [btEndDate, setBtEndDate] = useState('');
  const [btSymbols, setBtSymbols] = useState<string[]>(['XAUUSD', 'BTCUSD', 'XRPUSD', 'EURUSD']);
  const [btStatus, setBtStatus] = useState('');
  const [btError, setBtError] = useState('');
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const ALL_SYMBOLS = ['XAUUSD', 'BTCUSD', 'XRPUSD', 'EURUSD'];

  const toggleSymbol = (sym: string) => {
    setBtSymbols(prev =>
      prev.includes(sym)
        ? prev.length > 1 ? prev.filter(s => s !== sym) : prev  // keep at least 1
        : [...prev, sym]
    );
  };

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

  const handleRunBacktest = async () => {
    if (isRunningBacktest) return;
    setIsRunningBacktest(true);
    setBtStatus('Starting backtest…');
    setBtError('');

    // Clear any leftover poll
    if (pollRef.current) clearInterval(pollRef.current);

    const useCustomDates = btStartDate && btEndDate;

    try {
      await runBacktest({
        period: btPeriod,
        timeframe: '1d',
        initial_balance: 10000,
        symbols: btSymbols,
        start_date: useCustomDates ? btStartDate : null,
        end_date: useCustomDates ? btEndDate : null,
      });
      setBtStatus('Fetching data & simulating trades…');

      pollRef.current = setInterval(async () => {
        try {
          const status = await fetchBacktestStatus();
          if (!status.running && status.has_result) {
            clearInterval(pollRef.current!);
            pollRef.current = null;
            try {
              const result = await fetchBacktestResult();
              setBacktestResult(result);
              setBtStatus('');
            } catch (fetchErr: any) {
              setBtError(`Result load failed: ${fetchErr?.response?.data?.detail || fetchErr?.message || 'server error'}`);
            } finally {
              setIsRunningBacktest(false);
            }
          } else if (!status.running && !status.has_result) {
            // Backtest finished but no result — it errored out
            clearInterval(pollRef.current!);
            pollRef.current = null;
            setIsRunningBacktest(false);
            setBtStatus('');
            setBtError('Backtest failed — check backend logs.');
          }
        } catch {
          clearInterval(pollRef.current!);
          pollRef.current = null;
          setIsRunningBacktest(false);
          setBtStatus('');
          setBtError('Lost connection while polling.');
        }
      }, 2000);
    } catch (err: any) {
      setIsRunningBacktest(false);
      setBtStatus('');
      setBtError(err?.response?.data?.detail || 'Failed to start backtest.');
    }
  };

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
                  ['Risk / Trade', '1.0%'],
                  ['Max Trades/Day', '3'],
                  ['Daily Loss Cap', '3%'],
                  ['Max Drawdown', '8%'],
                  ['Min R:R', '1:1.5'],
                  ['Challenge Target', '10%'],
                ].map(([label, val]) => (
                  <div key={label} className="flex justify-between">
                    <span className="text-text-secondary">{label}</span>
                    <span className="text-accent-green font-semibold">{val}</span>
                  </div>
                ))}
              </div>
            </Card>

            {/* Run Backtest */}
            <Card>
              <CardHeader
                title="Backtest"
                subtitle={backtestResult ? `Last: ${(backtestResult.symbols || []).join(', ')} · ${backtestResult.start_date ? `${backtestResult.start_date} → ${backtestResult.end_date}` : backtestResult.period}` : 'Simulate over real historical data'}
              />
              <div className="space-y-3">

                {/* Symbol selector */}
                <div>
                  <p className="text-xs text-text-secondary mb-1.5">Symbols</p>
                  <div className="flex flex-wrap gap-1.5">
                    {ALL_SYMBOLS.map(sym => (
                      <button
                        key={sym}
                        onClick={() => toggleSymbol(sym)}
                        disabled={isRunningBacktest}
                        className={`px-2 py-1 rounded text-xs font-mono font-semibold transition-colors disabled:opacity-50 ${
                          btSymbols.includes(sym)
                            ? 'bg-accent-blue text-white'
                            : 'bg-bg-border text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        {sym}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Quick period buttons */}
                <div>
                  <p className="text-xs text-text-secondary mb-1.5">Quick Period</p>
                  <div className="flex gap-1.5">
                    {['1mo', '3mo', '6mo', '1y'].map(p => (
                      <button
                        key={p}
                        onClick={() => { setBtPeriod(p); setBtStartDate(''); setBtEndDate(''); }}
                        disabled={isRunningBacktest}
                        className={`flex-1 py-1 rounded text-xs font-mono transition-colors disabled:opacity-50 ${
                          btPeriod === p && !btStartDate
                            ? 'bg-accent-blue text-white font-semibold'
                            : 'bg-bg-border text-text-secondary hover:text-text-primary'
                        }`}
                      >
                        {p}
                      </button>
                    ))}
                  </div>
                </div>

                {/* Custom date range */}
                <div>
                  <p className="text-xs text-text-secondary mb-1.5">Custom Range <span className="opacity-50">(overrides period)</span></p>
                  <div className="grid grid-cols-2 gap-1.5">
                    <div>
                      <label className="block text-xs text-text-secondary mb-0.5">From</label>
                      <input
                        type="date"
                        value={btStartDate}
                        onChange={e => setBtStartDate(e.target.value)}
                        disabled={isRunningBacktest}
                        className="w-full bg-bg-secondary border border-bg-border rounded px-2 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-blue disabled:opacity-50"
                      />
                    </div>
                    <div>
                      <label className="block text-xs text-text-secondary mb-0.5">To</label>
                      <input
                        type="date"
                        value={btEndDate}
                        onChange={e => setBtEndDate(e.target.value)}
                        disabled={isRunningBacktest}
                        className="w-full bg-bg-secondary border border-bg-border rounded px-2 py-1 text-xs text-text-primary focus:outline-none focus:ring-1 focus:ring-accent-blue disabled:opacity-50"
                      />
                    </div>
                  </div>
                  {btStartDate && btEndDate && (
                    <p className="text-xs text-accent-blue mt-1">
                      Using custom range: {btStartDate} → {btEndDate}
                    </p>
                  )}
                </div>

                {/* Run button */}
                <button
                  onClick={handleRunBacktest}
                  disabled={isRunningBacktest || btSymbols.length === 0}
                  className="w-full flex items-center justify-center gap-2 px-4 py-2 rounded-md text-sm font-semibold bg-accent-blue text-white hover:bg-blue-500 transition-colors disabled:opacity-60 disabled:cursor-not-allowed"
                >
                  {isRunningBacktest
                    ? <><Loader2 className="w-4 h-4 animate-spin" /> Running…</>
                    : <><PlayCircle className="w-4 h-4" /> Run Backtest</>
                  }
                </button>

                {/* Status / Error */}
                {btStatus && <p className="text-xs text-text-secondary text-center">{btStatus}</p>}
                {btError && <p className="text-xs text-accent-red text-center">{btError}</p>}

                {/* Quick result summary */}
                {backtestResult && !isRunningBacktest && (
                  <div className="space-y-1 pt-1 border-t border-bg-border text-xs font-mono">
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Return</span>
                      <span className={backtestResult.total_return_pct >= 0 ? 'text-accent-green font-semibold' : 'text-accent-red font-semibold'}>
                        {backtestResult.total_return_pct > 0 ? '+' : ''}{backtestResult.total_return_pct?.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Win Rate</span>
                      <span className="text-text-primary">{backtestResult.win_rate_pct?.toFixed(1)}%</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Trades</span>
                      <span className="text-text-primary">{backtestResult.total_trades}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Max DD</span>
                      <span className={backtestResult.max_drawdown_pct < 5 ? 'text-accent-green' : backtestResult.max_drawdown_pct < 8 ? 'text-accent-yellow' : 'text-accent-red'}>
                        {backtestResult.max_drawdown_pct?.toFixed(2)}%
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Wins / Losses</span>
                      <span className="text-text-primary">{backtestResult.wins}W / {backtestResult.losses}L</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-text-secondary">Challenge</span>
                      <span className={backtestResult.challenge_passed ? 'text-accent-green font-semibold' : 'text-accent-yellow'}>
                        {backtestResult.challenge_passed ? 'Passed ✓' : 'In Progress'}
                      </span>
                    </div>
                  </div>
                )}
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
