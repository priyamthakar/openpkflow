interface Props {
  label: string
  value: string | number | null | undefined
  unit?: string
  highlight?: boolean
}

export function MetricCard({ label, value, unit, highlight }: Props) {
  const display = value == null || (typeof value === 'number' && !isFinite(value)) ? '—' : value

  return (
    <div
      style={{
        background: highlight ? 'var(--accent-muted)' : 'var(--surface)',
        border: `1px solid ${highlight ? 'rgba(94,106,210,0.3)' : 'var(--border)'}`,
        borderRadius: 'var(--radius)',
        padding: '14px 18px',
        minWidth: 120,
      }}
    >
      <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.06em', marginBottom: 6 }}>
        {label}
      </p>
      <p style={{ fontSize: 22, fontWeight: 600, color: highlight ? 'var(--accent)' : 'var(--text)' }}>
        {typeof display === 'number' ? display.toFixed(3) : display}
        {unit && <span style={{ fontSize: 12, color: 'var(--text-muted)', marginLeft: 4 }}>{unit}</span>}
      </p>
    </div>
  )
}
