import type { PasteDataColumn, PasteDataRow } from '@/components/shared/PasteDataGrid'

export function rowsToCsvFile(columns: PasteDataColumn[], rows: PasteDataRow[], filename: string): File {
  return new File([rowsToCsv(columns, rows)], filename, { type: 'text/csv' })
}

function rowsToCsv(columns: PasteDataColumn[], rows: PasteDataRow[]) {
  const header = columns.map((column) => escapeCsv(column.key)).join(',')
  const body = rows
    .filter((row) => columns.some((column) => String(row[column.key] ?? '').trim() !== ''))
    .map((row) => columns.map((column) => escapeCsv(row[column.key] ?? '')).join(','))
  return [header, ...body].join('\n')
}

function escapeCsv(value: string | number) {
  const text = String(value)
  return /[",\n]/.test(text) ? `"${text.replace(/"/g, '""')}"` : text
}
