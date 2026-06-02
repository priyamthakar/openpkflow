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
    <header className="h-12 px-4 lg:px-5 bg-surface border-b border-border flex items-center justify-between shrink-0">
      <div className="flex items-center gap-3 min-w-0">
        {onMenuClick && (
          <button
            type="button"
            onClick={onMenuClick}
            aria-label="Open sidebar"
            className="lg:hidden p-1 -ml-1 rounded-sm text-text-muted hover:text-text hover:bg-surface-2 transition-colors"
          >
            <Menu size={20} />
          </button>
        )}
        <div className="min-w-0">
          <h1 className="font-mono-ui text-[14px] font-semibold text-text uppercase tracking-[0.12em] truncate">
            {title}
          </h1>
          {subtitle && (
            <p className="text-[13px] text-text-muted truncate mt-0.5">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex items-center gap-3">
        <ThemeToggle />
        {data?.engine_version && (
          <Badge variant="accent">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-success animate-pulse" />
              engine v{data.engine_version}
            </span>
          </Badge>
        )}
        <a
          href="https://github.com/priyamthakar/openpkflow"
          target="_blank"
          rel="noreferrer"
          className="flex items-center gap-1.5 text-[13px] text-text-muted hover:text-text transition-colors no-underline"
        >
          GitHub
          <ExternalLink size={11} aria-hidden="true" />
        </a>
      </div>
    </header>
  )
}
