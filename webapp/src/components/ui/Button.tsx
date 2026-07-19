import { Loader2 } from 'lucide-react'
import { cn } from '@/lib/utils'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
}

export function Button({
  variant = 'primary',
  size = 'md',
  loading,
  className,
  children,
  disabled,
  ...props
}: ButtonProps) {
  return (
    <button
      className={cn(
        'inline-flex items-center justify-center rounded-sm font-medium transition-all duration-200',
        'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40 focus-visible:ring-offset-1',
        'disabled:cursor-not-allowed active:scale-[0.98]',
        variant === 'primary' &&
          'bg-accent text-accent-fg font-semibold hover:bg-accent-hover disabled:bg-surface-2 disabled:text-text-muted disabled:border disabled:border-border',
        variant === 'secondary' && 'bg-surface border border-border text-text hover:border-border-2 hover:bg-surface-2',
        variant === 'ghost' && 'text-text-muted hover:text-text hover:bg-surface-2',
        variant === 'danger' && 'bg-danger/10 text-danger border border-danger/30 hover:bg-danger/20',
        size === 'sm' && 'px-3 py-1.5 text-sm gap-1.5',
        size === 'md' && 'px-4 py-2 text-sm gap-2',
        size === 'lg' && 'px-6 py-2.5 text-base gap-2',
        className,
      )}
      disabled={disabled || loading}
      {...props}
    >
      {loading && <Loader2 size={16} className="animate-spin shrink-0" />}
      {children}
    </button>
  )
}
