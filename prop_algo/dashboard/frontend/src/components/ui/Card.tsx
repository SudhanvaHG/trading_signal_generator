import { clsx } from 'clsx';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  glow?: 'green' | 'red' | 'blue' | 'none';
}

export function Card({ children, className, glow = 'none' }: CardProps) {
  return (
    <div className={clsx(
      'bg-bg-card border border-bg-border rounded-xl p-4',
      glow === 'green' && 'shadow-[0_0_20px_rgba(0,200,150,0.08)]',
      glow === 'red'   && 'shadow-[0_0_20px_rgba(255,71,87,0.08)]',
      glow === 'blue'  && 'shadow-[0_0_20px_rgba(59,130,246,0.08)]',
      className,
    )}>
      {children}
    </div>
  );
}

export function CardHeader({ title, subtitle, action }: { title: string; subtitle?: string; action?: React.ReactNode }) {
  return (
    <div className="flex items-start justify-between mb-4">
      <div>
        <h3 className="text-text-primary font-semibold text-sm">{title}</h3>
        {subtitle && <p className="text-text-secondary text-xs mt-0.5">{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
}
