import { cn } from '@/lib/utils'
import { Skeleton } from '@/components/ui/Skeleton'

interface Props {
  label: string
  value: string | number | null | undefined
  unit?: string
  highlight?: boolean
  loading?: boolean
  className?: string
}

export function MetricCard({ label, value, unit, highlight, loading, className }: Props) {
  if (loading) return <Skeleton className="h-[88px] min-w-[140px]" />

  const hasValue = value != null && (typeof value !== 'number' || isFinite(value))

  return (
    <div
      className={cn(
        'flex-1 basis-[130px] rounded-sm border p-4 min-w-[130px] transition-all animate-fade-in',
        highlight
          ? 'border-accent/30 bg-accent-muted/50 border-l-[3px] border-l-accent'
          : 'border-border bg-surface hover:border-border-2',
        className,
      )}
    >
      <p className="text-[11px] font-semibold uppercase tracking-wider text-text-muted mb-1.5">
        {label}
      </p>
      <p className="text-[26px] font-bold text-text tabular-nums leading-tight">
        {hasValue ? (typeof value === 'number' ? value.toFixed(3) : value) : 'Not available'}
        {hasValue && unit && (
          <span className="text-sm font-medium text-text-muted ml-1">{unit}</span>
        )}
      </p>
    </div>
  )
}
