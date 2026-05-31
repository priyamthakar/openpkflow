import { useRef, useState, type DragEvent } from 'react'
import { Upload } from 'lucide-react'

interface Props {
  onFile: (f: File) => void
  accept?: string
  label?: string
}

export function FileDropzone({ onFile, accept = '.csv,.xlsx', label = 'Upload CSV / XLSX' }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const [file, setFile] = useState<File | null>(null)

  function handle(f: File) {
    setFile(f)
    onFile(f)
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    setOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handle(f)
  }

  return (
    <div
      onClick={() => inputRef.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setOver(true) }}
      onDragLeave={() => setOver(false)}
      onDrop={onDrop}
      style={{
        border: `2px dashed ${over ? 'var(--accent)' : 'var(--border-2)'}`,
        borderRadius: 'var(--radius)',
        padding: '28px 20px',
        textAlign: 'center',
        cursor: 'pointer',
        background: over ? 'var(--accent-muted)' : 'var(--surface)',
        transition: 'all 0.15s',
      }}
    >
      <Upload size={20} style={{ color: 'var(--text-muted)', margin: '0 auto 8px' }} />
      {file ? (
        <p style={{ color: 'var(--text)', fontSize: 13, fontWeight: 500 }}>
          {file.name} ({(file.size / 1024).toFixed(1)} KB)
        </p>
      ) : (
        <>
          <p style={{ color: 'var(--text)', fontSize: 13 }}>{label}</p>
          <p style={{ color: 'var(--text-dim)', fontSize: 11, marginTop: 4 }}>
            Drag &amp; drop or click — {accept}
          </p>
        </>
      )}
      <input ref={inputRef} type="file" accept={accept} style={{ display: 'none' }}
        onChange={(e) => { const f = e.target.files?.[0]; if (f) handle(f) }} />
    </div>
  )
}
