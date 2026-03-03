import { clsx } from 'clsx';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'green' | 'red' | 'blue' | 'yellow' | 'purple' | 'gray';
  size?: 'sm' | 'md';
  dot?: boolean;
}

const variants = {
  green:  'bg-accent-green/10 text-accent-green border-accent-green/20',
  red:    'bg-accent-red/10 text-accent-red border-accent-red/20',
  blue:   'bg-accent-blue/10 text-accent-blue border-accent-blue/20',
  yellow: 'bg-accent-yellow/10 text-accent-yellow border-accent-yellow/20',
  purple: 'bg-accent-purple/10 text-accent-purple border-accent-purple/20',
  gray:   'bg-text-muted/10 text-text-secondary border-text-muted/20',
};

export function Badge({ children, variant = 'gray', size = 'sm', dot }: BadgeProps) {
  return (
    <span className={clsx(
      'inline-flex items-center gap-1 rounded border font-mono font-semibold',
      size === 'sm' ? 'px-1.5 py-0.5 text-[10px]' : 'px-2 py-1 text-xs',
      variants[variant],
    )}>
      {dot && (
        <span className={clsx('w-1.5 h-1.5 rounded-full', {
          'bg-accent-green': variant === 'green',
          'bg-accent-red':   variant === 'red',
          'bg-accent-blue':  variant === 'blue',
          'bg-accent-yellow': variant === 'yellow',
        })} />
      )}
      {children}
    </span>
  );
}
