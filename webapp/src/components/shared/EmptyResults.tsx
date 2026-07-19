import type { LucideIcon } from 'lucide-react'

interface Props {
  icon: LucideIcon
  title: string
  description?: string
}

/**
 * Placeholder shown in a result pane before the first analysis run.
 * Previews the shape of the output (metrics + chart) without fake data.
 */
export function EmptyResults({ icon: Icon, title, description }: Props) {
  return (
    <div className="flex flex-col items-center justify-center gap-5 rounded-sm border border-dashed border-border-2 bg-surface/50 px-6 py-12 text-center">
      <div className="flex h-12 w-12 items-center justify-center rounded-sm bg-accent-muted text-accent">
        <Icon size={22} aria-hidden="true" />
      </div>
      <div className="max-w-sm">
        <p className="text-base font-semibold text-text">{title}</p>
        {description && <p className="mt-1.5 text-sm text-text-muted leading-relaxed">{description}</p>}
        <p className="mt-3 font-mono-ui text-[11px] uppercase tracking-[0.12em] text-text-dim">
          Ctrl+Enter to run
        </p>
      </div>
      <div className="w-full max-w-md space-y-3 opacity-45" aria-hidden="true">
        <div className="flex gap-3">
          <div className="h-16 flex-1 rounded-sm bg-surface-2" />
          <div className="h-16 flex-1 rounded-sm bg-surface-2" />
          <div className="h-16 flex-1 rounded-sm bg-surface-2" />
        </div>
        <div className="h-32 rounded-sm bg-surface-2" />
      </div>
    </div>
  )
}
