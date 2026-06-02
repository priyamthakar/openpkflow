/**
 * Typed API client. All calls go through /api (proxied to FastAPI in dev).
 * In production, VITE_API_URL should point to the deployed FastAPI backend.
 */

const BASE = import.meta.env.VITE_API_URL ?? ''

import type {
  BeResponse,
  CompareResponse,
  FormulationsResponse,
  HealthResponse,
  IvIvcResponse,
  NcaResponse,
  SimResponse,
} from './types'

async function _json<T>(res: Response): Promise<T> {
  const text = await res.text()
  const body = parseJsonBody(text)
  if (!res.ok) throw new Error(errorMessageFromResponse(res, body, text))
  if (body == null) return {} as T
  return body as T
}

function parseJsonBody(text: string): unknown {
  if (!text.trim()) return null
  try {
    return JSON.parse(text)
  } catch {
    return null
  }
}

function errorMessageFromResponse(res: Response, body: unknown, text: string) {
  if (body && typeof body === 'object' && 'detail' in body) {
    const detail = (body as { detail?: unknown }).detail
    if (typeof detail === 'string') return detail
    if (detail != null) return JSON.stringify(detail)
  }
  const cleaned = text.replace(/<[^>]*>/g, ' ').replace(/\s+/g, ' ').trim()
  const suffix = cleaned ? `: ${cleaned.slice(0, 180)}` : ''
  return `HTTP ${res.status} ${res.statusText || 'request failed'}${suffix}`
}

async function assertReportOk(res: Response) {
  if (res.ok) return
  const text = await res.text()
  const body = parseJsonBody(text)
  throw new Error(`Report failed: ${errorMessageFromResponse(res, body, text)}`)
}

// ---------- Health ----------
export async function fetchHealth(): Promise<HealthResponse> {
  return _json(await fetch(`${BASE}/health`))
}

// ---------- NCA ----------
export async function analyzeNca(file: File, options: object): Promise<NcaResponse> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('options', JSON.stringify(options))
  return _json(await fetch(`${BASE}/api/nca/analyze`, { method: 'POST', body: fd }))
}

export function ncaReportUrl(format: string): string {
  return `${BASE}/api/nca/report?format=${format}`
}

export async function downloadNcaReport(file: File, options: object, format: string): Promise<void> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('options', JSON.stringify(options))
  fd.append('format', format)
  const res = await fetch(`${BASE}/api/nca/report`, { method: 'POST', body: fd })
  await assertReportOk(res)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `nca_report.${ext}`)
}

// ---------- Dissolution ----------
export async function fetchFormulations(file: File, columns: object): Promise<FormulationsResponse> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('columns', JSON.stringify(columns))
  return _json(await fetch(`${BASE}/api/dissolution/formulations`, { method: 'POST', body: fd }))
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
  return _json(await fetch(`${BASE}/api/dissolution/compare`, { method: 'POST', body: fd }))
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
  const res = await fetch(`${BASE}/api/dissolution/report`, { method: 'POST', body: fd })
  await assertReportOk(res)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `dissolution_report.${ext}`)
}

// ---------- Simulation ----------
export async function simulate(req: object): Promise<SimResponse> {
  return _json(
    await fetch(`${BASE}/api/sim/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
  )
}

export async function downloadSimReport(req: object, format: string): Promise<void> {
  const params = new URLSearchParams({ format })
  const res = await fetch(`${BASE}/api/sim/report?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  await assertReportOk(res)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `sim_report.${ext}`)
}

// ---------- IVIVC ----------
export async function analyzeIvIvc(req: object): Promise<IvIvcResponse> {
  return _json(
    await fetch(`${BASE}/api/ivivc/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
  )
}

export async function downloadIvIvcReport(req: object, format: string): Promise<void> {
  const params = new URLSearchParams({ format })
  const res = await fetch(`${BASE}/api/ivivc/report?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  await assertReportOk(res)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `ivivc_report.${ext}`)
}

// ---------- BE ----------
export async function analyzeBe(file: File, options: object): Promise<BeResponse> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('options', JSON.stringify(options))
  return _json(await fetch(`${BASE}/api/be/analyze`, { method: 'POST', body: fd }))
}

export async function downloadBeReport(file: File, options: object, format: string): Promise<void> {
  const fd = new FormData()
  fd.append('file', file)
  fd.append('options', JSON.stringify(options))
  fd.append('format', format)
  const res = await fetch(`${BASE}/api/be/report`, { method: 'POST', body: fd })
  await assertReportOk(res)
  const blob = await res.blob()
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `be_report.${ext}`)
}

function _triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
