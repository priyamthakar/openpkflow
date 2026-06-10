import { ExternalLink, Menu } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { ThemeToggle } from './ThemeToggle'
import { Badge } from '@/components/ui/Badge'
import { fetchHealth } from '@/lib/api'

interface Props {
  title: string
  subtitle?: string
  onMenuClick?: () => void
}

export function TopBar({ title, subtitle, onMenuClick }: Props) {
  const { data } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    staleTime: 60_000,
  })

  return (
    <header className="min-h-14 px-3 py-2 sm:h-12 sm:px-4 sm:py-0 lg:px-5 bg-surface border-b border-border flex items-center justify-between gap-2 shrink-0">
      <div className="flex items-center gap-2 min-w-0 sm:gap-3">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Open sidebar"
            className="lg:hidden -ml-1 flex h-9 w-9 shrink-0 items-center justify-center rounded-sm text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
          >
            <Menu size={20} />
          </button>
        )}
        <div className="min-w-0">
          <h1 className="font-mono-ui truncate text-[12.5px] font-semibold uppercase tracking-[0.08em] text-text sm:text-[14px] sm:tracking-[0.12em]">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-0.5 truncate text-[12px] text-text-muted sm:text-[13px]">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1.5 sm:gap-3">
        <ThemeToggle />
        {data?.engine_version && (
          <Badge variant="accent">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
              <span className="sm:hidden">v{data.engine_version}</span>
              <span className="hidden sm:inline">engine v{data.engine_version}</span>
            </span>
          </Badge>
        )}
        <a
          href="https://github.com/priyamthakar/openpkflow"
          target="_blank"
          rel="noreferrer"
          className="hidden items-center gap-1.5 text-[13px] text-text-muted hover:text-text transition-colors no-underline sm:flex"
        >
          GitHub
          <ExternalLink size={11} aria-hidden="true" />
        </a>
      </div>
    </header>
  )
}
