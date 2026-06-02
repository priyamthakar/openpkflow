import { AlertTriangle, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  message: string
  onDismiss?: () => void
  className?: string
}

export function ErrorBanner({ message, onDismiss, className }: Props) {
  return (
    <div
      role="alert"
      className={cn(
        'flex items-start gap-3 rounded-sm border border-danger/30 bg-danger/5 p-3.5 text-danger animate-fade-in',
        className,
      )}
    >
      <AlertTriangle size={17} className="mt-0.5 shrink-0" />
      <p className="text-sm flex-1 leading-relaxed">{message}</p>
      {onDismiss && (
        <button
          onClick={onDismiss}
          aria-label="Dismiss error"
          className="shrink-0 p-0.5 rounded hover:bg-danger/10 transition-colors"
        >
          <X size={15} />
        </button>
      )}
    </div>
  )
}
