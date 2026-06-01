/**
 * Typed API client — all calls go through /api (proxied to FastAPI in dev).
 */

import type {
  CompareResponse,
  FormulationsResponse,
  HealthResponse,
  NcaResponse,
  SimResponse,
} from './types'

async function _json<T>(res: Response): Promise<T> {
  const body = await res.json()
  if (!res.ok) throw new Error(body?.detail ?? `HTTP ${res.status}`)
  return body as T
}

// ---------- Health ----------
export async function fetchHealth(): Promise<HealthResponse> {
  return _json(await fetch('/health'))
}

// ---------- NCA ----------
export async function analyzeNca(file: File, options: object): Promise<NcaResponse> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('options', JSON.stringify(options))
  return _json(await fetch('/api/nca/analyze', { method: 'POST', body: fd }))
}

export function ncaReportUrl(format: string): string {
  return `/api/nca/report?format=${format}`
}

export async function downloadNcaReport(file: File, options: object, format: string): Promise<void> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('options', JSON.stringify(options))
  fd.append('format', format)
  const res = await fetch('/api/nca/report', { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`Report failed: HTTP ${res.status}`)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `nca_report.${ext}`)
}

// ---------- Dissolution ----------
export async function fetchFormulations(file: File, columns: object): Promise<FormulationsResponse> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('columns', JSON.stringify(columns))
  return _json(await fetch('/api/dissolution/formulations', { method: 'POST', body: fd }))
}

export async function compareFormulations(
  file: File,
  reference: string,
  test: string,
  columns: object,
): Promise<CompareResponse> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('reference', reference)
  fd.append('test', test)
  fd.append('columns', JSON.stringify(columns))
  return _json(await fetch('/api/dissolution/compare', { method: 'POST', body: fd }))
}

export async function downloadDissolutionReport(
  file: File,
  reference: string,
  test: string,
  columns: object,
  format: string,
): Promise<void> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('reference', reference)
  fd.append('test', test)
  fd.append('columns', JSON.stringify(columns))
  fd.append('format', format)
  const res = await fetch('/api/dissolution/report', { method: 'POST', body: fd })
  if (!res.ok) throw new Error(`Report failed: HTTP ${res.status}`)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `dissolution_report.${ext}`)
}

// ---------- Simulation ----------
export async function simulate(req: object): Promise<SimResponse> {
  return _json(
    await fetch('/api/sim/simulate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
  )
}

export async function downloadSimReport(req: object, format: string): Promise<void> {
  const params = new URLSearchParams({ format })
  const res = await fetch(`/api/sim/report?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  if (!res.ok) throw new Error(`Report failed: HTTP ${res.status}`)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `sim_report.${ext}`)
}

function _triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
