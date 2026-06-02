import { useRef, useState, type DragEvent } from 'react'
import { Upload, FolderOpen, FileIcon, X } from 'lucide-react'
import { cn } from '@/lib/utils'

interface Props {
  onFile: (f: File) => void
  accept?: string
  label?: string
  maxSizeMB?: number
}

export function FileDropzone({ onFile, accept = '.csv', label = 'Upload CSV', maxSizeMB = 10 }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)
  const [over, setOver] = useState(false)
  const [file, setFile] = useState<File | null>(null)
  const [fileError, setFileError] = useState('')

  function handle(f: File) {
    setFileError('')
    if (maxSizeMB && f.size > maxSizeMB * 1024 * 1024) {
      setFileError(`File exceeds ${maxSizeMB} MB limit.`)
      return
    }
    const ext = '.' + f.name.split('.').pop()?.toLowerCase()
    const allowed = accept.split(',').map((s) => s.trim().toLowerCase())
    if (!allowed.includes(ext)) {
      setFileError(`Unsupported file type. Accepted: ${accept}`)
      return
    }
    setFile(f)
    onFile(f)
  }

  function onDragOver(e: DragEvent) {
    e.preventDefault()
    setOver(true)
  }

  function onDragLeave() {
    setOver(false)
  }

  function onDrop(e: DragEvent) {
    e.preventDefault()
    setOver(false)
    const f = e.dataTransfer.files[0]
    if (f) handle(f)
  }

  function clear() {
    setFile(null)
    setFileError('')
    if (inputRef.current) inputRef.current.value = ''
  }

  const Icon = over ? FolderOpen : file ? FileIcon : Upload

  return (
    <div>
      <div
        role="button"
        tabIndex={0}
        aria-label="Drop a file here or press Enter to browse"
        onKeyDown={(e) => {
          if (e.key === 'Enter' || e.key === ' ') inputRef.current?.click()
        }}
        onClick={() => inputRef.current?.click()}
        onDragOver={onDragOver}
        onDragLeave={onDragLeave}
        onDrop={onDrop}
        className={cn(
          'relative rounded-sm border-2 border-dashed p-8 text-center cursor-pointer transition-all duration-200',
          'focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40',
          over
            ? 'border-accent bg-accent-muted scale-[1.01]'
            : fileError
              ? 'border-danger/50 bg-danger/5'
              : file
                ? 'border-success/50 bg-success/5'
                : 'border-border-2 bg-surface hover:border-border hover:bg-surface-2',
        )}
      >
        <Icon
          size={28}
          className={cn(
            'mx-auto mb-3 transition-colors',
            over ? 'text-accent' : fileError ? 'text-danger' : 'text-text-muted',
          )}
        />
        {file ? (
          <div className="space-y-1">
            <p className="text-text text-sm font-semibold">{file.name}</p>
            <p className="text-text-muted text-xs font-medium">{(file.size / 1024).toFixed(1)} KB</p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation()
                clear()
              }}
              className="inline-flex items-center gap-1 mt-2 text-xs text-text-muted hover:text-danger transition-colors"
            >
              <X size={12} />
              Remove
            </button>
          </div>
        ) : (
          <>
            <p className="text-text text-base font-semibold">{label}</p>
            <p className="text-text-muted text-sm font-medium mt-1.5">
              Drag &amp; drop or click. Accepted: {accept}
            </p>
          </>
        )}
        <input
          ref={inputRef}
          type="file"
          accept={accept}
          className="hidden"
          onChange={(e) => {
            const f = e.target.files?.[0]
            if (f) handle(f)
          }}
        />
      </div>

      {fileError && (
        <p className="mt-2 text-xs text-danger flex items-center gap-1">
          <X size={12} />
          {fileError}
        </p>
      )}
    </div>
  )
}
