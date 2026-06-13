import { cn } from '@/lib/utils'

interface SegmentedControlProps<T extends string> {
  value: T
  onChange: (value: T) => void
  options: { value: T; label: string }[]
  className?: string
}

export function SegmentedControl<T extends string>({
  value,
  onChange,
  options,
  className,
}: SegmentedControlProps<T>) {
  return (
    <div
      className={cn(
        'flex w-full bg-surface-2 rounded-sm p-1 border border-border sm:inline-flex sm:w-auto',
        className,
      )}
      role="radiogroup"
    >
      {options.map((o) => (
        <button
          key={o.value}
          type="button"
          role="radio"
          aria-checked={value === o.value}
          onClick={() => onChange(o.value)}
          className={cn(
            'min-w-0 flex-1 px-3 py-1.5 text-sm font-medium rounded-sm transition-all duration-150 sm:flex-none sm:px-4',
            'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40',
            value === o.value
              ? 'bg-surface text-text shadow-sm'
              : 'text-text hover:bg-surface/60',
          )}
        >
          {o.label}
        </button>
      ))}
    </div>
  )
}
