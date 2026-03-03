'use client';
import { useEffect, useState } from 'react';
import { Header } from '@/components/dashboard/Header';
import { Card, CardHeader } from '@/components/ui/Card';
import { Button } from '@/components/ui/Button';
import { Badge } from '@/components/ui/Badge';
import { StatCard } from '@/components/ui/StatCard';
import { EquityCurveChart } from '@/components/charts/EquityCurveChart';
import { StrategyBarChart, AssetPieChart } from '@/components/charts/StrategyBreakdownChart';
import { SignalTable } from '@/components/dashboard/SignalTable';
import { useStore } from '@/store/useStore';
import { runBacktest, fetchBacktestResult, fetchBacktestStatus, fetchTradeLog } from '@/lib/api';
import { FlaskConical, Trophy, AlertTriangle, TrendingUp, TrendingDown } from 'lucide-react';
import toast from 'react-hot-toast';

const PERIODS    = ['1mo','3mo','6mo','1y','2y'];
const TIMEFRAMES = ['1d','4h','1h'];

export default function BacktestPage() {
  const { backtestResult, setBacktestResult, backtestRunning, setBacktestRunning, backtestProgress, backtestProgressMsg } = useStore();
  const [period, setPeriod]   = useState('1y');
  const [tf, setTf]           = useState('1d');
  const [balance, setBalance] = useState(10000);
  const [tradeLog, setTradeLog]= useState<any[]>([]);
  const [tab, setTab]         = useState<'overview'|'signals'|'trades'>('overview');

  useEffect(() => {
    fetchBacktestStatus().then(s => {
      if (s.has_result) fetchBacktestResult().then(setBacktestResult).catch(()=>{});
    }).catch(()=>{});
  }, []);

  const handleRun = async () => {
    setBacktestRunning(true);
    try {
      await runBacktest({ period, timeframe: tf, initial_balance: balance });
      toast.success('Backtest started — results coming via WebSocket...');
    } catch (e: any) {
      toast.error(e?.response?.data?.detail || 'Backtest failed to start');
      setBacktestRunning(false);
    }
  };

  // Poll for result when running
  useEffect(() => {
    if (!backtestRunning) return;
    const timer = setInterval(async () => {
      try {
        const status = await fetchBacktestStatus();
        if (!status.running && status.has_result) {
          const result = await fetchBacktestResult();
          setBacktestResult(result);
          setBacktestRunning(false);
          clearInterval(timer);
        }
      } catch {}
    }, 3000);
    return () => clearInterval(timer);
  }, [backtestRunning]);

  const r = backtestResult;
  const returnColor = r && r.total_return_pct >= 0 ? 'green' : 'red';

  return (
    <div className="animate-fade-in">
      <Header title="Backtest" subtitle="Historical strategy simulation" />
      <div className="p-6 space-y-6">

        {/* Config */}
        <Card>
          <CardHeader title="Run Configuration" subtitle="Select parameters and run the backtest" />
          <div className="flex flex-wrap items-end gap-5">
            <div>
              <label className="text-text-secondary text-[10px] uppercase tracking-wider block mb-1.5">Period</label>
              <div className="flex gap-1">
                {PERIODS.map(p => (
                  <button key={p} onClick={() => setPeriod(p)}
                    className={`px-3 py-1.5 rounded text-xs font-mono border transition-all ${period===p?'bg-accent-blue/10 text-accent-blue border-accent-blue/30':'border-bg-border text-text-secondary hover:border-bg-hover'}`}>
                    {p}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-text-secondary text-[10px] uppercase tracking-wider block mb-1.5">Timeframe</label>
              <div className="flex gap-1">
                {TIMEFRAMES.map(t => (
                  <button key={t} onClick={() => setTf(t)}
                    className={`px-3 py-1.5 rounded text-xs font-mono border transition-all ${tf===t?'bg-accent-blue/10 text-accent-blue border-accent-blue/30':'border-bg-border text-text-secondary hover:border-bg-hover'}`}>
                    {t}
                  </button>
                ))}
              </div>
            </div>
            <div>
              <label className="text-text-secondary text-[10px] uppercase tracking-wider block mb-1.5">Initial Balance ($)</label>
              <input
                type="number" value={balance} onChange={e => setBalance(Number(e.target.value))}
                min={1000} max={1000000} step={1000}
                className="w-32 bg-bg-border border border-bg-border text-text-primary text-sm rounded-lg px-3 py-1.5 font-mono"
              />
            </div>
            <Button
              variant="primary" size="md"
              icon={<FlaskConical className="w-4 h-4" />}
              onClick={handleRun}
              loading={backtestRunning}
            >
              {backtestRunning ? 'Running...' : 'Run Backtest'}
            </Button>
          </div>

          {/* Progress bar */}
          {backtestRunning && (
            <div className="mt-5">
              <div className="flex justify-between text-xs font-mono text-text-secondary mb-1.5">
                <span>{backtestProgressMsg || 'Processing...'}</span>
                <span>{backtestProgress}%</span>
              </div>
              <div className="h-1.5 bg-bg-border rounded-full overflow-hidden">
                <div
                  className="h-full bg-accent-blue rounded-full transition-all duration-500"
                  style={{ width: `${backtestProgress}%` }}
                />
              </div>
            </div>
          )}
        </Card>

        {/* Results */}
        {r && (
          <>
            {/* KPIs */}
            <div className="grid grid-cols-2 sm:grid-cols-4 xl:grid-cols-7 gap-4">
              <StatCard title="Return" value={`${r.total_return_pct>0?'+':''}${r.total_return_pct?.toFixed(2)}%`}
                color={returnColor} trend={r.total_return_pct>0?'up':'down'}
                sub={`$${r.final_balance?.toLocaleString()}`} icon={r.total_return_pct>0?<TrendingUp className="w-4 h-4"/>:<TrendingDown className="w-4 h-4"/>} />
              <StatCard title="Win Rate" value={`${r.win_rate_pct?.toFixed(1)}%`}
                color={r.win_rate_pct>=50?'green':'red'} sub={`${r.wins}W / ${r.losses}L`} />
              <StatCard title="Total Trades" value={r.total_trades} color="blue" />
              <StatCard title="Max DD" value={`${r.max_drawdown_pct?.toFixed(2)}%`}
                color={r.max_drawdown_pct<5?'green':r.max_drawdown_pct<8?'yellow':'red'}
                icon={<AlertTriangle className="w-4 h-4"/>} />
              <StatCard title="Initial" value={`$${r.initial_balance?.toLocaleString()}`} color="white" />
              <StatCard title="Final" value={`$${r.final_balance?.toLocaleString()}`} color={returnColor} />
              <StatCard title="Challenge"
                value={r.challenge_passed?'PASSED':'In Progress'}
                color={r.challenge_passed?'green':'yellow'}
                icon={<Trophy className="w-4 h-4"/>} />
            </div>

            {/* Tabs */}
            <div className="flex gap-1 border-b border-bg-border">
              {(['overview','signals','trades'] as const).map(t => (
                <button key={t} onClick={() => setTab(t)}
                  className={`px-4 py-2 text-sm capitalize transition-all border-b-2 -mb-px ${tab===t?'text-accent-blue border-accent-blue':'text-text-secondary border-transparent hover:text-text-primary'}`}>
                  {t}
                </button>
              ))}
            </div>

            {tab === 'overview' && (
              <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
                <Card>
                  <CardHeader title="Equity Curve" subtitle={`${r.period} ${r.timeframe} backtest`}
                    action={r.challenge_passed ? <Badge variant="green">Challenge ✓</Badge> : <Badge variant="yellow">In Progress</Badge>} />
                  <EquityCurveChart data={r.equity_curve || []} initialBalance={r.initial_balance} />
                </Card>
                <Card>
                  <CardHeader title="Signals by Strategy" />
                  <StrategyBarChart data={r.strategy_breakdown || {}} />
                </Card>
                <Card>
                  <CardHeader title="Signals by Asset" />
                  <AssetPieChart data={r.asset_breakdown || {}} />
                </Card>
                <Card>
                  <CardHeader title="Summary Stats" />
                  <div className="space-y-2 text-sm font-mono">
                    {[
                      ['Period', r.period],
                      ['Timeframe', r.timeframe],
                      ['Run At', new Date(r.run_at).toLocaleString()],
                      ['Total Signals', r.approved_signals_count],
                      ['Wins', r.wins],
                      ['Losses', r.losses],
                      ['Win Rate', `${r.win_rate_pct?.toFixed(1)}%`],
                      ['Max Drawdown', `${r.max_drawdown_pct?.toFixed(2)}%`],
                      ['Return', `${r.total_return_pct?.toFixed(2)}%`],
                      ['Challenge Target', `${r.challenge_target_pct}%`],
                      ['Challenge Status', r.challenge_passed ? '✅ PASSED' : r.account_blown ? '💀 BLOWN' : '⏳ In Progress'],
                    ].map(([k, v]) => (
                      <div key={k} className="flex justify-between border-b border-bg-border/50 py-1">
                        <span className="text-text-secondary">{k}</span>
                        <span className={`font-semibold ${v === '✅ PASSED' ? 'text-accent-green' : v === '💀 BLOWN' ? 'text-accent-red' : 'text-text-primary'}`}>{v}</span>
                      </div>
                    ))}
                  </div>
                </Card>
              </div>
            )}

            {tab === 'signals' && (
              <Card>
                <CardHeader title="Approved Signals" subtitle={`${r.approved_signals?.length ?? 0} signals used in backtest`} />
                <SignalTable signals={r.approved_signals || []} />
              </Card>
            )}

            {tab === 'trades' && (
              <Card>
                <CardHeader title="Trade Log" subtitle={`${r.trade_log?.length ?? 0} simulated trades`} />
                <div className="overflow-x-auto">
                  <table className="w-full text-xs font-mono">
                    <thead>
                      <tr className="border-b border-bg-border text-text-secondary text-[10px] uppercase">
                        {['#','Date','Symbol','Strategy','Dir','Entry','SL','TP','RR','Result','P&L%','Balance','DD%'].map(h => (
                          <th key={h} className="text-left py-2 px-2">{h}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody>
                      {(r.trade_log || []).map((t: any, i: number) => (
                        <tr key={i} className="border-b border-bg-border/40 hover:bg-bg-hover/40">
                          <td className="py-1.5 px-2 text-text-secondary">{i+1}</td>
                          <td className="py-1.5 px-2 text-text-secondary">{t.timestamp?.toString().slice(0,10)}</td>
                          <td className="py-1.5 px-2 font-semibold">{t.symbol}</td>
                          <td className="py-1.5 px-2 text-text-secondary truncate max-w-[120px]">{t.strategy?.replace('_',' ')}</td>
                          <td className="py-1.5 px-2">
                            <Badge variant={t.signal==='BUY'?'green':'red'}>{t.signal}</Badge>
                          </td>
                          <td className="py-1.5 px-2">{Number(t.entry).toFixed(4)}</td>
                          <td className="py-1.5 px-2 text-accent-red">{Number(t.sl).toFixed(4)}</td>
                          <td className="py-1.5 px-2 text-accent-green">{Number(t.tp).toFixed(4)}</td>
                          <td className="py-1.5 px-2">1:{Number(t.rr).toFixed(1)}</td>
                          <td className="py-1.5 px-2">
                            <Badge variant={t.result==='WIN'?'green':'red'}>{t.result}</Badge>
                          </td>
                          <td className={`py-1.5 px-2 font-semibold ${t.pnl_pct>0?'text-accent-green':'text-accent-red'}`}>
                            {t.pnl_pct>0?'+':''}{Number(t.pnl_pct).toFixed(2)}%
                          </td>
                          <td className="py-1.5 px-2">${Number(t.balance).toLocaleString()}</td>
                          <td className={`py-1.5 px-2 ${Number(t.drawdown_pct)>5?'text-accent-red':Number(t.drawdown_pct)>2?'text-accent-yellow':'text-text-secondary'}`}>
                            {Number(t.drawdown_pct).toFixed(2)}%
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </Card>
            )}
          </>
        )}

        {!r && !backtestRunning && (
          <Card>
            <div className="flex flex-col items-center justify-center py-20 text-text-secondary">
              <FlaskConical className="w-12 h-12 mb-4 opacity-30" />
              <p className="text-base font-medium mb-1">No backtest results yet</p>
              <p className="text-sm">Configure the parameters above and click <strong>Run Backtest</strong></p>
            </div>
          </Card>
        )}
      </div>
    </div>
  );
}
