import { clsx } from 'clsx';

interface StatCardProps {
  title: string;
  value: string | number;
  sub?: string;
  color?: 'green' | 'red' | 'blue' | 'yellow' | 'purple' | 'white';
  icon?: React.ReactNode;
  trend?: 'up' | 'down' | null;
}

const colors = {
  green:  'text-accent-green',
  red:    'text-accent-red',
  blue:   'text-accent-blue',
  yellow: 'text-accent-yellow',
  purple: 'text-accent-purple',
  white:  'text-text-primary',
};

export function StatCard({ title, value, sub, color = 'white', icon, trend }: StatCardProps) {
  return (
    <div className="bg-bg-card border border-bg-border rounded-xl p-4 flex flex-col gap-1">
      <div className="flex items-center justify-between">
        <p className="text-text-secondary text-xs font-medium uppercase tracking-wider">{title}</p>
        {icon && <span className="text-text-secondary">{icon}</span>}
      </div>
      <p className={clsx('text-2xl font-bold font-mono', colors[color])}>{value}</p>
      {sub && (
        <p className={clsx('text-xs', trend === 'up' ? 'text-accent-green' : trend === 'down' ? 'text-accent-red' : 'text-text-secondary')}>
          {trend === 'up' ? '▲ ' : trend === 'down' ? '▼ ' : ''}{sub}
        </p>
      )}
    </div>
  );
}
