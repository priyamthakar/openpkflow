import { AlertCircle } from 'lucide-react'

export function ErrorBanner({ message }: { message: string }) {
  return (
    <div
      style={{
        display: 'flex',
        alignItems: 'flex-start',
        gap: 10,
        padding: '12px 16px',
        background: 'rgba(229,83,75,0.08)',
        border: '1px solid rgba(229,83,75,0.3)',
        borderRadius: 'var(--radius)',
        color: 'var(--danger)',
        fontSize: 13,
      }}
    >
      <AlertCircle size={15} style={{ marginTop: 2, flexShrink: 0 }} />
      <span>{message}</span>
    </div>
  )
}
