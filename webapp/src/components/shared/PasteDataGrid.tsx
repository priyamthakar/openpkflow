import type React from 'react'
import { Trash2 } from 'lucide-react'
import { cn } from '@/lib/utils'

export interface PasteDataColumn {
  key: string
  label: string
  type?: 'string' | 'number'
}

export type PasteDataRow = Record<string, string | number>

interface Props {
  columns: PasteDataColumn[]
  rows: PasteDataRow[]
  onChange: (rows: PasteDataRow[]) => void
  filename: string
  hint?: string
}

export function PasteDataGrid({ columns, rows, onChange, filename, hint }: Props) {
  function updateCell(rowIndex: number, key: string, value: string) {
    onChange(rows.map((row, i) => (i === rowIndex ? { ...row, [key]: value } : row)))
  }

  function addRow(afterIndex: number) {
    const empty = columns.reduce<PasteDataRow>((acc, c) => {
      acc[c.key] = ''
      return acc
    }, {})
    const next = [...rows]
    next.splice(afterIndex + 1, 0, empty)
    onChange(next)
  }

  function deleteRow(rowIndex: number) {
    if (rows.length <= 1) return
    onChange(rows.filter((_, i) => i !== rowIndex))
  }

  function handlePaste(e: React.ClipboardEvent<HTMLDivElement>) {
    const text = e.clipboardData.getData('text')
    const pasted = parseGridText(text, columns)
    if (pasted.length === 0) return
    e.preventDefault()
    onChange(pasted)
  }

  function copyCsv() {
    void navigator.clipboard.writeText(rowsToCsv(columns, rows))
  }

  return (
    <section
      onPaste={handlePaste}
      className="bg-surface border border-border rounded-sm overflow-hidden"
    >
      <div className="flex justify-between items-center gap-3 px-3 py-2.5 border-b border-border">
        <div>
          <h3 className="text-sm font-semibold text-text">Paste / edit table</h3>
          <p className="text-text-muted text-[12px] mt-0.5">
            {hint ?? 'Paste tabular data from Excel or Prism. Headers are optional.'}
          </p>
        </div>
        <button
          type="button"
          onClick={copyCsv}
          className="px-2.5 py-1 text-xs border border-border-2 bg-surface-2 text-text rounded-sm hover:border-accent transition-colors"
        >
          Copy CSV
        </button>
      </div>

      <div className="overflow-x-auto max-h-[400px] overflow-y-auto">
        <table
          className="w-full border-collapse text-sm"
          style={{ minWidth: columns.length * 120 }}
          role="grid"
          aria-label="Editable data grid"
        >
          <thead className="sticky top-0 z-10">
            <tr>
              <th className="w-10 px-2 py-2 bg-surface-2 text-text text-left border-b border-border font-semibold text-xs">
                #
              </th>
              {columns.map((column) => (
                <th
                  key={column.key}
                  className="px-2.5 py-2 bg-surface-2 text-text text-left border-b border-border font-semibold text-xs whitespace-nowrap"
                >
                  {column.label}
                </th>
              ))}
              <th className="w-10 px-1 py-2 bg-surface-2 border-b border-border" />
            </tr>
          </thead>
          <tbody>
            {rows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={cn(
                  'group transition-colors',
                  rowIndex % 2 === 0 ? 'bg-transparent' : 'bg-white/[0.02]',
                )}
              >
                <td className="px-2 py-1.5 text-text-muted text-xs text-right tabular-nums">
                  {rowIndex + 1}
                </td>
                {columns.map((column) => {
                  const value = row[column.key] ?? ''
                  const strVal = String(value)
                  const invalid =
                    column.type === 'number' && strVal.trim() !== '' && !Number.isFinite(Number(strVal))
                  return (
                    <td key={column.key} className="px-1 py-1">
                      <input
                        value={strVal}
                        onChange={(e) => updateCell(rowIndex, column.key, e.target.value)}
                        className={cn(
                          'w-full bg-surface-2 border rounded-sm px-2 py-1.5 text-sm font-medium text-text',
                          'focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent',
                          invalid
                            ? 'border-danger/60 bg-danger/5'
                            : 'border-border-2',
                        )}
                        aria-label={`${column.label}, row ${rowIndex + 1}`}
                      />
                    </td>
                  )
                })}
                <td className="px-1 py-1">
                  <div className="flex gap-0.5">
                    <button
                      type="button"
                      onClick={() => addRow(rowIndex)}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-surface-2 text-text-dim hover:text-accent transition-all text-xs leading-none"
                      title="Insert row below"
                      aria-label={`Insert row below row ${rowIndex + 1}`}
                    >
                      +
                    </button>
                    <button
                      type="button"
                      onClick={() => deleteRow(rowIndex)}
                      disabled={rows.length <= 1}
                      className="opacity-0 group-hover:opacity-100 p-1 rounded hover:bg-danger/10 text-text-dim hover:text-danger transition-all text-xs leading-none disabled:opacity-0"
                      title="Delete row"
                      aria-label={`Delete row ${rowIndex + 1}`}
                    >
                      <Trash2 size={12} />
                    </button>
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex justify-between items-center gap-2 px-3 py-2 border-t border-border">
        <span className="text-text-muted text-xs">
          {rows.length} row{rows.length !== 1 ? 's' : ''} ready for {filename}
        </span>
        <div className="flex gap-2">
          <button
            type="button"
            onClick={() => addRow(rows.length - 1)}
            className="px-2.5 py-1 text-xs border border-border-2 bg-surface-2 text-text rounded-sm hover:border-accent transition-colors"
          >
            Add row
          </button>
        </div>
      </div>
    </section>
  )
}

function rowsToCsv(columns: PasteDataColumn[], rows: PasteDataRow[]) {
  const header = columns.map((c) => escapeCsv(c.key)).join(',')
  const body = rows
    .filter((row) => columns.some((c) => String(row[c.key] ?? '').trim() !== ''))
    .map((row) => columns.map((c) => escapeCsv(row[c.key] ?? '')).join(','))
  return [header, ...body].join('\n')
}

function escapeCsv(value: string | number) {
  const text = String(value)
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}

function parseGridText(text: string, columns: PasteDataColumn[]) {
  const lines = text.trim().split(/\r?\n/).filter(Boolean)
  if (lines.length === 0) return []

  const matrix = lines.map((line) => splitCells(line))
  const first = matrix[0].map((cell) => normalize(cell))
  const keys = columns.map((c) => normalize(c.key))
  const labels = columns.map((c) => normalize(c.label))
  const hasHeader = first.some((cell) => keys.includes(cell) || labels.includes(cell))
  const dataRows = hasHeader ? matrix.slice(1) : matrix
  const order = hasHeader
    ? first.map((cell, i) => columnIndexFor(cell, columns) ?? i)
    : columns.map((_, i) => i)

  return dataRows.map((cells) => {
    const row = columns.reduce<PasteDataRow>((acc, c) => {
      acc[c.key] = ''
      return acc
    }, {})
    cells.forEach((cell, i) => {
      const ci = order[i]
      const col = columns[ci]
      if (col) row[col.key] = cell.trim()
    })
    return row
  })
}

function splitCells(line: string) {
  return line.includes('\t') ? line.split('\t') : line.split(',')
}

function columnIndexFor(cell: string, columns: PasteDataColumn[]) {
  const normalized = normalize(cell)
  const idx = columns.findIndex(
    (c) => normalize(c.key) === normalized || normalize(c.label) === normalized,
  )
  return idx >= 0 ? idx : undefined
}

function normalize(value: string) {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '_')
    .replace(/^_|_$/g, '')
}
