import { ShieldAlert } from 'lucide-react'

export function Disclaimer({ text }: { text?: string }) {
  return (
    <div
      style={{
        display: 'flex',
        gap: 10,
        padding: '10px 14px',
        background: 'rgba(240,167,49,0.06)',
        border: '1px solid rgba(240,167,49,0.2)',
        borderRadius: 'var(--radius)',
        fontSize: 11,
        color: 'var(--text-muted)',
        lineHeight: 1.5,
      }}
    >
      <ShieldAlert size={13} style={{ marginTop: 2, flexShrink: 0, color: 'var(--warning)' }} />
      <span>
        {text ??
          'This output was generated using OpenPKFlow (open-source). Final regulatory interpretation should be reviewed by qualified experts.'}
      </span>
    </div>
  )
}
