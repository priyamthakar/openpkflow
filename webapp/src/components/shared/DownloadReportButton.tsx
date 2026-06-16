import { useEffect, useState } from 'react'
import { createPortal } from 'react-dom'
import { Download, ChevronDown, Globe, FileText, FileType, FileCode, Eye, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  onDownload: (format: string) => Promise<void>
  formats?: string[]
}

const ALL_FORMATS = [
  { value: 'html', label: 'HTML Report', icon: Globe },
  { value: 'pdf', label: 'PDF Report', icon: FileText },
  { value: 'docx', label: 'Word (.docx)', icon: FileType },
  { value: 'markdown', label: 'Markdown', icon: FileCode },
]

export function DownloadReportButton({ onDownload, formats }: Props) {
  const FORMATS = formats ? ALL_FORMATS.filter((f) => formats.includes(f.value)) : ALL_FORMATS
  const [loading, setLoading] = useState(false)
  const [formatLoading, setFormatLoading] = useState<string | null>(null)
  const [open, setOpen] = useState(false)
  const [previewOpen, setPreviewOpen] = useState(false)
  const [error, setError] = useState('')
  const primaryFormat = FORMATS[0]?.value ?? 'html'

  useEffect(() => {
    if (!open && !previewOpen) return
    function onKeyDown(event: KeyboardEvent) {
      if (event.key !== 'Escape') return
      setOpen(false)
      setPreviewOpen(false)
    }
    window.addEventListener('keydown', onKeyDown)
    return () => window.removeEventListener('keydown', onKeyDown)
  }, [open, previewOpen])

  async function handle(fmt: string) {
    setOpen(false)
    setLoading(true)
    setFormatLoading(fmt)
    setError('')
    try {
      await onDownload(fmt)
    } catch (e) {
      console.error(e)
      setError((e as Error).message)
    } finally {
      setLoading(false)
      setFormatLoading(null)
    }
  }

  return (
    <div className="relative flex w-full flex-col items-stretch gap-2 sm:inline-flex sm:w-auto sm:items-start">
      <div className="flex w-full flex-col items-stretch gap-2 sm:w-auto sm:flex-row">
        <button
          type="button"
          onClick={() => {
            setOpen(false)
            setPreviewOpen(true)
          }}
          className={cn(
            'flex items-center gap-2 rounded-sm border border-border-2 px-4 py-2',
            'bg-surface text-text text-sm font-semibold hover:border-accent transition-colors',
          )}
        >
          <Eye size={15} />
          Preview report
        </button>
        <div className="flex w-full items-stretch overflow-hidden rounded-sm border border-border-2 sm:w-auto">
        <button
          onClick={() => handle(primaryFormat)}
          disabled={loading}
          className={cn(
            'flex flex-1 items-center justify-center gap-2 px-4 py-2 bg-surface-2 text-text text-sm font-semibold sm:flex-none',
            'border-0 cursor-pointer transition-colors hover:bg-surface',
            loading && 'opacity-60 cursor-not-allowed',
          )}
        >
          <Download size={15} className={loading ? 'animate-pulse' : ''} />
          {loading ? 'Generating...' : 'Download Report'}
        </button>
        <button
          onClick={() => setOpen((o) => !o)}
          className="px-2.5 bg-surface-2 text-text-muted border-l border-border cursor-pointer hover:text-text transition-colors"
          aria-label="Choose report format"
          aria-expanded={open}
        >
          <ChevronDown size={16} className={cn('transition-transform', open && 'rotate-180')} />
        </button>
        </div>
      </div>
      {error && <p className="text-xs text-danger">{error}</p>}

      {open && (
        <>
          <div className="fixed inset-0 z-40" onClick={() => setOpen(false)} />
          <div className="absolute left-0 top-full z-50 mt-1.5 w-full min-w-[190px] animate-fade-in overflow-hidden rounded-sm border border-border bg-surface shadow-lg sm:left-auto sm:right-0 sm:w-auto">
            {FORMATS.map((f) => {
              const Icon = f.icon
              return (
                <button
                  key={f.value}
                  onClick={() => handle(f.value)}
                  disabled={loading}
                  className={cn(
                    'w-full flex items-center gap-2.5 px-4 py-2.5 text-left text-sm text-text',
                    'hover:bg-surface-2 transition-colors border-0 bg-transparent cursor-pointer',
                    loading && 'opacity-50 cursor-not-allowed',
                    formatLoading === f.value && 'bg-accent-muted',
                  )}
                >
                  <Icon size={15} className={cn(formatLoading === f.value && 'animate-spin')} />
                  {f.label}
                </button>
              )
            })}
          </div>
        </>
      )}

      {previewOpen && createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-2 sm:p-4">
          <div
            className="relative z-10 max-h-[calc(100dvh-1rem)] w-full max-w-2xl overflow-y-auto rounded-sm border border-border shadow-2xl"
            style={{ backgroundColor: 'var(--surface)' }}
          >
            <div className="flex items-center justify-between border-b border-border px-4 py-3">
              <div>
                <h3 className="text-sm font-semibold text-text">Report preview</h3>
                <p className="text-xs font-medium text-text-muted">
                  Generate a shareable report in the selected format.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setPreviewOpen(false)}
                className="rounded-sm p-1.5 text-text-muted hover:bg-surface-2 hover:text-text"
                aria-label="Close report preview"
              >
                <X size={16} />
              </button>
            </div>

            <div className="grid gap-4 p-3 sm:p-4 md:grid-cols-[1fr_220px]">
              <div className="hidden min-h-[260px] border border-border bg-bg p-4 sm:block">
                <div className="mb-4 h-5 w-40 bg-surface-2" />
                <div className="space-y-2">
                  <div className="h-3 w-full bg-surface-2" />
                  <div className="h-3 w-5/6 bg-surface-2" />
                  <div className="h-3 w-3/4 bg-surface-2" />
                </div>
                <div className="mt-6 grid grid-cols-3 gap-2">
                  <div className="h-16 border border-border bg-surface" />
                  <div className="h-16 border border-border bg-surface" />
                  <div className="h-16 border border-border bg-surface" />
                </div>
                <div className="mt-4 h-28 border border-border bg-surface" />
                <p className="mt-4 text-xs leading-relaxed text-text-muted">
                  Report includes the current results, warnings, summary metrics, plots, and
                  OpenPKFlow regulatory-review disclaimer.
                </p>
              </div>

              <div className="space-y-2">
                <p className="mb-3 text-sm leading-relaxed text-text-muted sm:hidden">
                  Choose a report format for the current analysis results.
                </p>
                {FORMATS.map((f) => {
                  const Icon = f.icon
                  return (
                    <button
                      key={f.value}
                      type="button"
                      onClick={() => handle(f.value)}
                      disabled={loading}
                      className={cn(
                        'flex w-full items-center gap-2 rounded-sm border border-border px-3 py-2',
                        'bg-surface-2 text-left text-sm font-semibold text-text hover:border-accent',
                        loading && 'opacity-60',
                      )}
                    >
                      <Icon size={15} />
                      {formatLoading === f.value ? 'Generating...' : f.label}
                    </button>
                  )
                })}
              </div>
            </div>
          </div>
        </div>,
        document.body,
      )}
    </div>
  )
}
