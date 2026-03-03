import { clsx } from 'clsx';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger' | 'ghost' | 'success';
  size?: 'sm' | 'md' | 'lg';
  loading?: boolean;
  icon?: React.ReactNode;
}

const variants = {
  primary:   'bg-accent-blue hover:bg-accent-blue/80 text-white border-accent-blue/30',
  secondary: 'bg-bg-hover hover:bg-bg-border text-text-primary border-bg-border',
  danger:    'bg-accent-red/10 hover:bg-accent-red/20 text-accent-red border-accent-red/30',
  ghost:     'bg-transparent hover:bg-bg-hover text-text-secondary border-transparent',
  success:   'bg-accent-green/10 hover:bg-accent-green/20 text-accent-green border-accent-green/30',
};

const sizes = {
  sm: 'px-3 py-1.5 text-xs',
  md: 'px-4 py-2 text-sm',
  lg: 'px-6 py-3 text-base',
};

export function Button({
  children, variant = 'secondary', size = 'md',
  loading, icon, className, disabled, ...props
}: ButtonProps) {
  return (
    <button
      className={clsx(
        'inline-flex items-center gap-2 rounded-lg border font-medium transition-all duration-150',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant], sizes[size], className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : icon}
      {children}
    </button>
  );
}
