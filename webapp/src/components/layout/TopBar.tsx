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

/**
 * Render free-tier cold starts routinely fail the first health probe.
 * Retry with long delays and keep polling while offline so the badge recovers
 * once the API finishes waking (instead of sticking on "engine offline").
 */
const HEALTH_RETRY_DELAYS_MS = [2_000, 5_000, 10_000, 15_000, 20_000]

export function TopBar({ title, subtitle, onMenuClick }: Props) {
  const { data, isError, isLoading, isFetching, failureCount, refetch, error } = useQuery({
    queryKey: ['health'],
    queryFn: fetchHealth,
    staleTime: 60_000,
    // Default React Query retries are too short for Render cold starts (~30-60s).
    retry: HEALTH_RETRY_DELAYS_MS.length,
    retryDelay: (attempt) =>
      HEALTH_RETRY_DELAYS_MS[Math.min(attempt, HEALTH_RETRY_DELAYS_MS.length - 1)],
    // Recover automatically after a cold-start failure without a full page reload.
    refetchInterval: (query) => (query.state.status === 'error' ? 15_000 : false),
    refetchOnWindowFocus: true,
  })

  const waking = isError || (isFetching && !data)
  const online = Boolean(data?.engine_version) && !isError
  const errorHint =
    error instanceof Error
      ? error.message
      : 'API unreachable. Click to retry (Render may be cold-starting).'

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
          <h1 className="font-mono-ui truncate text-[12px] font-semibold uppercase tracking-[0.04em] text-text min-[380px]:text-[12.5px] sm:text-[14px] sm:tracking-[0.12em]">
            {title}
          </h1>
          {subtitle && (
            <p className="mt-0.5 hidden truncate text-[13px] text-text-muted sm:block">{subtitle}</p>
          )}
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1 sm:gap-3">
        <ThemeToggle />
        {isError && (
          <button
            type="button"
            onClick={() => void refetch()}
            title={errorHint}
            className="rounded-sm border-0 bg-transparent p-0 cursor-pointer"
            aria-label="Retry engine health check"
          >
            <Badge variant="danger">
              <span className="flex items-center gap-1.5">
                <span
                  className={
                    isFetching
                      ? 'w-1.5 h-1.5 rounded-full bg-warning animate-pulse'
                      : 'w-1.5 h-1.5 rounded-full bg-danger'
                  }
                />
                <span className="sm:hidden">{isFetching ? 'retry' : 'offline'}</span>
                <span className="hidden sm:inline">
                  {isFetching
                    ? 'waking engine...'
                    : failureCount > 0
                      ? 'engine offline · retry'
                      : 'engine offline'}
                </span>
              </span>
            </Badge>
          </button>
        )}
        {!isError && (isLoading || online) && (
          <Badge variant="accent">
            <span className="flex items-center gap-1.5">
              <span
                className={
                  waking
                    ? 'w-1.5 h-1.5 rounded-full bg-text-dim animate-pulse'
                    : 'w-1.5 h-1.5 rounded-full bg-success animate-pulse'
                }
              />
              <span className="sm:hidden">
                {isLoading || isFetching ? '...' : `v${data?.engine_version ?? ''}`}
              </span>
              <span className="hidden sm:inline">
                {isLoading || (isFetching && !data)
                  ? 'connecting...'
                  : `engine v${data?.engine_version ?? ''}`}
              </span>
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
