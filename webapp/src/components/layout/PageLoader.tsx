import { Loader2 } from 'lucide-react'

export function PageLoader() {
  return (
    <div className="flex items-center justify-center h-full min-h-[50vh]">
      <div className="flex flex-col items-center gap-3 text-text-muted">
        <Loader2 size={32} className="animate-spin text-accent" />
        <span className="text-sm font-medium">Loading...</span>
      </div>
    </div>
  )
}
