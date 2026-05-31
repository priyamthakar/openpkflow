import { useState } from 'react'
import { Download, ChevronDown } from 'lucide-react'

interface Props {
  onDownload: (format: string) => Promise<void>
}

const FORMATS = [
  { value: 'html', label: 'HTML Report' },
  { value: 'pdf', label: 'PDF Report' },
  { value: 'docx', label: 'Word (.docx)' },
  { value: 'markdown', label: 'Markdown' },
]

export function DownloadReportButton({ onDownload }: Props) {
  const [loading, setLoading] = useState(false)
  const [open, setOpen] = useState(false)

  async function handle(fmt: string) {
    setOpen(false)
    setLoading(true)
    try {
      await onDownload(fmt)
    } catch (e) {
      console.error(e)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div style={{ position: 'relative', display: 'inline-block' }}>
      <div style={{ display: 'flex', alignItems: 'stretch', borderRadius: 6, overflow: 'hidden', border: '1px solid var(--border-2)' }}>
        <button
          onClick={() => handle('html')}
          disabled={loading}
          style={{
            display: 'flex', alignItems: 'center', gap: 6,
            padding: '8px 14px', background: 'var(--surface-2)',
            color: 'var(--text)', fontSize: 13, cursor: loading ? 'not-allowed' : 'pointer',
            border: 'none', opacity: loading ? 0.6 : 1,
          }}
        >
          <Download size={14} />
          {loading ? 'Generating…' : 'Download Report'}
        </button>
        <button
          onClick={() => setOpen((o) => !o)}
          style={{
            padding: '8px 10px', background: 'var(--surface-2)',
            color: 'var(--text-muted)',
            cursor: 'pointer', border: 'none', borderLeft: '1px solid var(--border)',
          }}
        >
          <ChevronDown size={13} />
        </button>
      </div>

      {open && (
        <div style={{
          position: 'absolute', top: '100%', right: 0, marginTop: 4,
          background: 'var(--surface-2)', border: '1px solid var(--border)',
          borderRadius: 6, minWidth: 160, zIndex: 50, overflow: 'hidden',
        }}>
          {FORMATS.map((f) => (
            <button key={f.value} onClick={() => handle(f.value)}
              style={{
                display: 'block', width: '100%', textAlign: 'left',
                padding: '9px 14px', background: 'none', border: 'none',
                color: 'var(--text)', fontSize: 13, cursor: 'pointer',
              }}
            >
              {f.label}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}
