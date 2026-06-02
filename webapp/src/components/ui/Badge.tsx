import type { ReactNode } from 'react'
import { cn } from '@/lib/utils'
import { CheckCircle2, XCircle, AlertTriangle } from 'lucide-react'

interface BadgeProps {
  variant?: 'default' | 'success' | 'warning' | 'danger' | 'accent'
  children: ReactNode
  dot?: boolean
}

export function Badge({ variant = 'default', children, dot }: BadgeProps) {
  return (
    <span
      className={cn(
        'inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium',
        variant === 'default' && 'bg-surface-2 text-text-muted border border-border',
        variant === 'success' && 'bg-success/10 text-success border border-success/30',
        variant === 'warning' && 'bg-warning/10 text-warning border border-warning/30',
        variant === 'danger' && 'bg-danger/10 text-danger border border-danger/30',
        variant === 'accent' && 'bg-accent-muted text-accent border border-accent/30',
      )}
    >
      {variant === 'success' && <CheckCircle2 size={12} />}
      {variant === 'danger' && <XCircle size={12} />}
      {variant === 'warning' && <AlertTriangle size={12} />}
      {dot && variant === 'default' && <span className="w-1.5 h-1.5 rounded-full bg-text-dim" />}
      {children}
    </span>
  )
}
