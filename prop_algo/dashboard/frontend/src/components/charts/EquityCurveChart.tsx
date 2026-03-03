'use client';
import {
  ResponsiveContainer, AreaChart, Area, XAxis, YAxis,
  CartesianGrid, Tooltip, ReferenceLine,
} from 'recharts';

interface EquityCurveChartProps {
  data: any[];
  initialBalance: number;
}

const CustomTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  const d = payload[0]?.payload;
  return (
    <div className="bg-bg-card border border-bg-border rounded-lg p-3 text-xs font-mono shadow-xl">
      <p className="text-text-secondary mb-1">Trade #{label}</p>
      <p className="text-accent-green font-bold">${d?.balance?.toLocaleString()}</p>
      {d?.result && (
        <p className={d.result === 'WIN' ? 'text-accent-green' : 'text-accent-red'}>
          {d.result} {d.pnl_pct > 0 ? '+' : ''}{d.pnl_pct?.toFixed(2)}%
        </p>
      )}
      {d?.symbol && <p className="text-text-secondary">{d.symbol}</p>}
      {d?.drawdown > 0 && <p className="text-accent-red">DD: -{d.drawdown?.toFixed(2)}%</p>}
    </div>
  );
};

export function EquityCurveChart({ data, initialBalance }: EquityCurveChartProps) {
  if (!data?.length) return (
    <div className="flex items-center justify-center h-64 text-text-secondary text-sm">
      No equity curve data
    </div>
  );

  const maxBalance = Math.max(...data.map(d => d.balance));
  const minBalance = Math.min(...data.map(d => d.balance));
  const padding = (maxBalance - minBalance) * 0.1;

  return (
    <ResponsiveContainer width="100%" height={280}>
      <AreaChart data={data} margin={{ top: 8, right: 8, bottom: 0, left: 8 }}>
        <defs>
          <linearGradient id="balGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%"  stopColor="#00C896" stopOpacity={0.25} />
            <stop offset="95%" stopColor="#00C896" stopOpacity={0} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke="#1E2D3D" strokeDasharray="3 3" vertical={false} />
        <XAxis
          dataKey="trade" tick={{ fill: '#64748B', fontSize: 10 }}
          axisLine={{ stroke: '#1E2D3D' }} tickLine={false}
          label={{ value: 'Trades', position: 'insideBottom', fill: '#64748B', fontSize: 10 }}
        />
        <YAxis
          domain={[minBalance - padding, maxBalance + padding]}
          tick={{ fill: '#64748B', fontSize: 10 }}
          axisLine={{ stroke: '#1E2D3D' }} tickLine={false}
          tickFormatter={(v) => `$${(v / 1000).toFixed(1)}k`}
          width={52}
        />
        <Tooltip content={<CustomTooltip />} />
        <ReferenceLine y={initialBalance} stroke="#374151" strokeDasharray="4 4" />
        <Area
          type="monotone" dataKey="balance"
          stroke="#00C896" strokeWidth={2}
          fill="url(#balGrad)" dot={false} activeDot={{ r: 4, fill: '#00C896' }}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
