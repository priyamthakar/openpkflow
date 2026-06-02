import { cn } from '@/lib/utils'

export function Select({
  className,
  children,
  ...props
}: React.SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      {...props}
      className={cn(
        'border rounded-sm px-3 py-2 text-sm font-semibold',
        'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent',
        'transition-all disabled:opacity-50',
        className,
      )}
    >
      {children}
    </select>
  )
}
