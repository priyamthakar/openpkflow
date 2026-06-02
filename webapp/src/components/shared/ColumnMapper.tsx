export interface RequiredColumn {
  key: string
  label: string
  default: string
}

interface ColumnMapperProps {
  headers: string[]
  required: RequiredColumn[]
  value: Record<string, string>
  onChange: (mapping: Record<string, string>) => void
}

export function ColumnMapper({ headers, required, value, onChange }: ColumnMapperProps) {
  function updateColumn(key: string, selected: string) {
    const next = { ...value, [key]: selected }
    onChange(next)
  }

  if (headers.length === 0) return null

  return (
    <div className="flex flex-col gap-2 p-3 bg-surface border border-border rounded-sm">
      {required.map((col) => (
        <label key={col.key} className="flex justify-between items-center gap-3">
          <span className="text-sm font-semibold text-text">{col.label}</span>
          <select
            value={value[col.key] ?? ''}
            onChange={(e) => updateColumn(col.key, e.target.value)}
            className="bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent min-w-[140px]"
          >
            {headers.map((header) => (
              <option key={header} value={header}>
                {header}
              </option>
            ))}
          </select>
        </label>
      ))}
    </div>
  )
}
