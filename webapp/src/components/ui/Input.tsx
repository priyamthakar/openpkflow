import { cn } from '@/lib/utils'

export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        'w-full bg-surface-2 border border-border-2 rounded-sm px-3 py-2 text-sm font-semibold text-text',
        'placeholder:text-text-dim',
        'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent',
        'transition-all disabled:opacity-50 disabled:cursor-not-allowed',
        className,
      )}
      {...props}
    />
  )
}
