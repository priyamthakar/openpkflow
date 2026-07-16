/**
 * Typed API client. All calls go through /api (proxied to FastAPI in dev).
 * In production, VITE_API_URL should point to the deployed FastAPI backend.
 */

const BASE = import.meta.env.VITE_API_URL ?? ''

import type {
  BePowerRequest,
  BePowerResponse,
  BeResponse,
  BeSampleSizeRequest,
  BeSampleSizeResponse,
  CompareResponse,
  FormulationsResponse,
  HealthResponse,
  IvIvcResponse,
  MultiMediaRequest,
  MultiMediaResponse,
  NcaResponse,
  PipelineFiles,
  PipelineOptions,
  PipelineResponse,
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

async function reportBlobForDownload(res: Response, format: string): Promise<Blob> {
  if (format !== 'html') return res.blob()
  const html = await res.text()
  return new Blob([makeHtmlReportMobileFriendly(html)], { type: 'text/html;charset=utf-8' })
}

function makeHtmlReportMobileFriendly(html: string): string {
  if (html.includes('data-openpkflow-mobile-download="true"')) return html

  const doc = new DOMParser().parseFromString(html, 'text/html')
  if (!doc.querySelector('meta[name="viewport"]')) {
    const meta = doc.createElement('meta')
    meta.setAttribute('name', 'viewport')
    meta.setAttribute('content', 'width=device-width, initial-scale=1.0')
    doc.head.prepend(meta)
  }
  doc.querySelectorAll('table').forEach((table) => {
    const headers = Array.from(table.querySelectorAll('thead th')).map((th) =>
      (th.textContent ?? '').replace(/\s+/g, ' ').trim(),
    )
    if (headers.length === 0) return
    table.querySelectorAll('tbody tr').forEach((row) => {
      Array.from(row.querySelectorAll('td')).forEach((cell, index) => {
        if (!cell.hasAttribute('data-label')) {
          cell.setAttribute('data-label', headers[index] ?? 'Value')
        }
      })
    })
  })

  const style = doc.createElement('style')
  style.setAttribute('data-openpkflow-mobile-download', 'true')
  style.textContent = `
@media (max-width: 640px) {
  body { margin: 0 !important; background: #ffffff !important; font-size: 13px !important; }
  .page { width: 100% !important; max-width: none !important; margin: 0 !important; border-radius: 0 !important; box-shadow: none !important; }
  .report-header { padding: 22px 18px 20px !important; }
  .report-header .org-label { font-size: 10px !important; letter-spacing: .09em !important; overflow-wrap: anywhere !important; }
  .report-header h1 { font-size: 20px !important; overflow-wrap: anywhere !important; }
  .meta-grid { grid-template-columns: 1fr !important; gap: 8px !important; }
  .content { padding: 28px 18px !important; }
  h2 { font-size: 12px !important; letter-spacing: .06em !important; overflow-wrap: anywhere !important; }
  table, thead, tbody, th, td, tr { display: block !important; }
  thead { display: none !important; }
  tbody tr {
    background: #ffffff !important;
    border: 1px solid #dce7f4 !important;
    border-radius: 6px !important;
    margin-bottom: 12px !important;
    overflow: hidden !important;
  }
  tbody tr:nth-child(even) { background: #ffffff !important; }
  tbody td {
    display: grid !important;
    grid-template-columns: minmax(112px, 45%) 1fr !important;
    gap: 12px !important;
    align-items: baseline !important;
    padding: 9px 12px !important;
    text-align: right !important;
    overflow-wrap: anywhere !important;
  }
  tbody td::before {
    content: attr(data-label) !important;
    color: #0d3b66 !important;
    font-size: 10px !important;
    font-weight: 700 !important;
    letter-spacing: .05em !important;
    text-align: left !important;
    text-transform: uppercase !important;
  }
  .report-footer, .footer {
    display: flex !important;
    flex-wrap: wrap !important;
    align-items: flex-start !important;
    gap: 6px 18px !important;
    padding: 14px 18px !important;
    overflow-wrap: anywhere !important;
    text-align: left !important;
  }
  img, svg, canvas { max-width: 100% !important; height: auto !important; }
}`
  doc.head.appendChild(style)
  return `<!doctype html>\n${doc.documentElement.outerHTML}`
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
  const blob = await reportBlobForDownload(res, format)
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
  const blob = await reportBlobForDownload(res, format)
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
  const blob = await reportBlobForDownload(res, format)
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
  const blob = await reportBlobForDownload(res, format)
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
  const blob = await reportBlobForDownload(res, format)
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `be_report.${ext}`)
}

export async function computeBePower(req: BePowerRequest): Promise<BePowerResponse> {
  return _json(
    await fetch(`${BASE}/api/be/power`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
  )
}

export async function computeBeSampleSize(req: BeSampleSizeRequest): Promise<BeSampleSizeResponse> {
  return _json(
    await fetch(`${BASE}/api/be/sample-size`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
  )
}

// ---------- Multi-media dissolution ----------
export async function analyzeMultiMedia(req: MultiMediaRequest): Promise<MultiMediaResponse> {
  return _json(
    await fetch(`${BASE}/api/dissolution/multi-media/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(req),
    }),
  )
}

export async function downloadMultiMediaReport(req: MultiMediaRequest, format: string): Promise<void> {
  const params = new URLSearchParams({ format })
  const res = await fetch(`${BASE}/api/dissolution/multi-media/report?${params}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
  })
  await assertReportOk(res)
  const blob = await reportBlobForDownload(res, format)
  _triggerDownload(blob, `multi_media_report.${format}`)
}

// ---------- Study pipeline ----------
function pipelineFormData(files: PipelineFiles, options: PipelineOptions): FormData {
  const fd = new FormData()
  fd.append('options', JSON.stringify(options))
  if (files.dissolution) fd.append('dissolution_file', files.dissolution)
  if (files.nca) fd.append('nca_file', files.nca)
  if (files.be) fd.append('be_file', files.be)
  return fd
}

export async function analyzePipeline(
  files: PipelineFiles,
  options: PipelineOptions,
): Promise<PipelineResponse> {
  return _json(
    await fetch(`${BASE}/api/pipeline/analyze`, {
      method: 'POST',
      body: pipelineFormData(files, options),
    }),
  )
}

export async function downloadPipelineReport(
  files: PipelineFiles,
  options: PipelineOptions,
  format: string,
): Promise<void> {
  const fd = pipelineFormData(files, options)
  fd.append('format', format)
  const res = await fetch(`${BASE}/api/pipeline/report`, { method: 'POST', body: fd })
  await assertReportOk(res)
  const blob = await reportBlobForDownload(res, format)
  const ext = format === 'markdown' ? 'md' : format
  _triggerDownload(blob, `study_pipeline_report.${ext}`)
}

export async function downloadPipelineAuditBundle(
  files: PipelineFiles,
  options: PipelineOptions,
): Promise<void> {
  const res = await fetch(`${BASE}/api/pipeline/audit-bundle`, {
    method: 'POST',
    body: pipelineFormData(files, options),
  })
  await assertReportOk(res)
  _triggerDownload(await res.blob(), 'openpkflow_audit_bundle.zip')
}

function _triggerDownload(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}
