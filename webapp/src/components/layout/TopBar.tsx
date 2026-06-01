import { ExternalLink } from 'lucide-react'
import { useQuery } from '@tanstack/react-query'
import { fetchHealth } from '@/lib/api'

interface Props {
  title: string
  subtitle?: string
}

export function TopBar({ title, subtitle }: Props) {
  const { data } = useQuery({ queryKey: ['health'], queryFn: fetchHealth, staleTime: 60_000 })

  return (
    <header
      style={{
        height: 56,
        padding: '0 28px',
        background: 'var(--surface)',
        borderBottom: '1px solid var(--border)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexShrink: 0,
      }}
    >
      <div>
        <h1 style={{ fontSize: 15, fontWeight: 600, color: 'var(--text)' }}>{title}</h1>
        {subtitle && <p style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 1 }}>{subtitle}</p>}
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
        {data && (
          <span
            style={{
              fontSize: 11,
              padding: '3px 8px',
              background: 'var(--accent-muted)',
              color: 'var(--accent)',
              borderRadius: 4,
              border: '1px solid rgba(94,106,210,0.3)',
            }}
          >
            engine v{data.engine_version}
          </span>
        )}
        <a
          href="https://github.com/priyamthakar/openpkflow"
          target="_blank"
          rel="noreferrer"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 5,
            color: 'var(--text-muted)',
            fontSize: 12,
            textDecoration: 'none',
          }}
        >
          GitHub <ExternalLink size={12} />
        </a>
      </div>
    </header>
  )
}
