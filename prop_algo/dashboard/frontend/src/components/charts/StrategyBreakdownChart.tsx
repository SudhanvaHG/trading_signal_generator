'use client';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, Cell, PieChart, Pie, Legend,
} from 'recharts';

const COLORS = ['#00C896', '#3B82F6', '#8B5CF6', '#F59E0B', '#FF4757'];

export function StrategyBarChart({ data }: { data: Record<string, any> }) {
  const chartData = Object.entries(data || {}).map(([name, val]: [string, any]) => ({
    name: name.replace('_', ' '),
    total: val.total,
    buy: val.buy || 0,
    sell: val.sell || 0,
    confidence: Math.round((val.avg_confidence || 0) * 100),
  }));

  if (!chartData.length) return <div className="flex items-center justify-center h-48 text-text-secondary text-sm">No data</div>;

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={chartData} margin={{ top: 8, right: 8, bottom: 0, left: 0 }}>
        <CartesianGrid stroke="#1E2D3D" strokeDasharray="3 3" vertical={false} />
        <XAxis dataKey="name" tick={{ fill: '#64748B', fontSize: 10 }} axisLine={false} tickLine={false} />
        <YAxis tick={{ fill: '#64748B', fontSize: 10 }} axisLine={false} tickLine={false} />
        <Tooltip
          contentStyle={{ background: '#141D2B', border: '1px solid #1E2D3D', borderRadius: 8, fontSize: 11, fontFamily: 'monospace' }}
          labelStyle={{ color: '#E0E6ED' }}
        />
        <Bar dataKey="buy" name="BUY" fill="#00C896" radius={[3, 3, 0, 0]} />
        <Bar dataKey="sell" name="SELL" fill="#FF4757" radius={[3, 3, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

export function AssetPieChart({ data }: { data: Record<string, any> }) {
  const chartData = Object.entries(data || {}).map(([name, val]: [string, any]) => ({
    name,
    value: val.total,
  }));

  if (!chartData.length) return <div className="flex items-center justify-center h-48 text-text-secondary text-sm">No data</div>;

  return (
    <ResponsiveContainer width="100%" height={220}>
      <PieChart>
        <Pie
          data={chartData} dataKey="value" nameKey="name"
          cx="50%" cy="50%" innerRadius={55} outerRadius={85}
          paddingAngle={3} strokeWidth={0}
        >
          {chartData.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Legend
          formatter={(value) => <span style={{ color: '#64748B', fontSize: 11 }}>{value}</span>}
        />
        <Tooltip
          contentStyle={{ background: '#141D2B', border: '1px solid #1E2D3D', borderRadius: 8, fontSize: 11 }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
