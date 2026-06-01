import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { TopBar } from '@/components/layout/TopBar'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { analyzeNca, downloadNcaReport } from '@/lib/api'
import type { NcaResponse } from '@/lib/types'

const AUC_METHODS = ['linear', 'log', 'linear_up_log_down'] as const
const BLQ_METHODS = ['none', 'drop', 'zero', 'half_lloq', 'lloq'] as const

export function NcaPage() {
  const [file, setFile] = useState<File | null>(null)
  const [aucMethod, setAucMethod] = useState<string>('linear')
  const [blqMethod, setBlqMethod] = useState<string>('none')
  const [steadyState, setSteadyState] = useState(false)
  const [tau, setTau] = useState<number>(12)
  const [selectedSubject, setSelectedSubject] = useState<string>('')

  const mutation = useMutation<NcaResponse, Error>({
    mutationFn: () =>
      analyzeNca(file!, { auc_method: aucMethod, blq_method: blqMethod, steady_state: steadyState, tau: steadyState ? tau : undefined }),
    onSuccess: (data) => {
      if (data.subjects.length > 0) setSelectedSubject(String(data.subjects[0].subject))
    },
  })

  const result = mutation.data
  const profile = result?.profiles.find((p) => p.subject === selectedSubject)
  const subjectRow = result?.subjects.find((r) => String(r.subject) === selectedSubject)

  const options = { auc_method: aucMethod, blq_method: blqMethod, steady_state: steadyState, tau: steadyState ? tau : undefined }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar title="Non-Compartmental Analysis" subtitle="Upload a PK CSV, configure options, and run NCA" />

      <div style={{ flex: 1, overflowY: 'auto', padding: 28, display: 'flex', gap: 24 }}>
        {/* Left panel */}
        <div style={{ width: 300, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <section>
            <SectionLabel>1. Upload Data</SectionLabel>
            <FileDropzone onFile={setFile} />
          </section>

          <section>
            <SectionLabel>2. Options</SectionLabel>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
              <Label text="AUC Method">
                <Select value={aucMethod} onChange={setAucMethod} options={AUC_METHODS as unknown as string[]} />
              </Label>
              <Label text="BLQ Method">
                <Select value={blqMethod} onChange={setBlqMethod} options={BLQ_METHODS as unknown as string[]} />
              </Label>
              <Label text="Steady State">
                <input type="checkbox" checked={steadyState} onChange={(e) => setSteadyState(e.target.checked)} />
              </Label>
              {steadyState && (
                <Label text="Tau (dosing interval)">
                  <input type="number" value={tau} onChange={(e) => setTau(Number(e.target.value))}
                    style={inputStyle} />
                </Label>
              )}
            </div>
          </section>

          <button
            onClick={() => mutation.mutate()}
            disabled={!file || mutation.isPending}
            style={btnStyle(!file || mutation.isPending)}
          >
            {mutation.isPending ? 'Analysing…' : 'Run NCA'}
          </button>
        </div>

        {/* Right panel */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {mutation.isError && <ErrorBanner message={mutation.error.message} />}

          {result && (
            <>
              {/* Warnings */}
              {result.warnings.length > 0 && (
                <WarningBox warnings={result.warnings} />
              )}

              {/* Subject selector + metrics */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                <label style={{ fontSize: 12, color: 'var(--text-muted)' }}>Subject:</label>
                <select
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  style={{ ...inputStyle, minWidth: 100 }}
                >
                  {result.subjects.map((r) => (
                    <option key={String(r.subject)} value={String(r.subject)}>
                      {String(r.subject)}
                    </option>
                  ))}
                </select>
              </div>

              {subjectRow && (
                <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                  <MetricCard label="AUClast" value={subjectRow.AUClast as number} />
                  <MetricCard label="AUCinf" value={subjectRow.AUCinf_obs as number} />
                  <MetricCard label="Cmax" value={subjectRow.Cmax as number} highlight />
                  <MetricCard label="Tmax" value={subjectRow.Tmax as number} unit="h" />
                  <MetricCard label="t½" value={subjectRow.half_life as number} unit="h" />
                  {subjectRow.CL_F != null && <MetricCard label="CL/F" value={subjectRow.CL_F as number} />}
                  {subjectRow.CL != null && <MetricCard label="CL" value={subjectRow.CL as number} />}
                </div>
              )}

              {/* Profile chart */}
              {profile && (
                <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 20 }}>
                  <h3 style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                    Concentration-Time Profile — Subject {selectedSubject}
                  </h3>
                  <PKChart
                    series={[{ name: `Subject ${selectedSubject}`, times: profile.times, concs: profile.concs }]}
                    xLabel="Time (h)"
                    yLabel="Concentration"
                    lambdaZ={{ times: profile.lambda_z_times, concs: profile.lambda_z_concs }}
                  />
                </div>
              )}

              {/* Summary table */}
              <ResultTable columns={result.columns} rows={result.subjects} />

              <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                <DownloadReportButton onDownload={(fmt) => downloadNcaReport(file!, options, fmt)} />
              </div>

              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

/* ---- Small helpers ---- */
function SectionLabel({ children }: { children: string }) {
  return <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>{children}</p>
}

function Label({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
      <span style={{ fontSize: 12, color: 'var(--text-muted)', flexShrink: 0 }}>{text}</span>
      {children}
    </div>
  )
}

function Select({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} style={{ ...inputStyle, minWidth: 140 }}>
      {options.map((o) => <option key={o} value={o}>{o}</option>)}
    </select>
  )
}

function WarningBox({ warnings }: { warnings: string[] }) {
  return (
    <div style={{ padding: '10px 14px', background: 'rgba(240,167,49,0.06)', border: '1px solid rgba(240,167,49,0.2)', borderRadius: 'var(--radius)', fontSize: 12, color: 'var(--warning)' }}>
      <p style={{ fontWeight: 600, marginBottom: 4 }}>Warnings</p>
      {warnings.map((w, i) => <p key={i}>• {w}</p>)}
    </div>
  )
}

function ResultTable({ columns, rows }: { columns: string[]; rows: Record<string, unknown>[] }) {
  const KEY_COLS = ['subject', 'AUClast', 'AUCinf_obs', 'Cmax', 'Tmax', 'half_life', 'CL_F', 'CL', 'Vz_F', 'Vz']
  const shown = KEY_COLS.filter((c) => columns.includes(c))
  return (
    <div style={{ overflowX: 'auto', borderRadius: 'var(--radius)', border: '1px solid var(--border)' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 12 }}>
        <thead>
          <tr>
            {shown.map((c) => (
              <th key={c} style={{ padding: '8px 12px', background: 'var(--surface)', color: 'var(--text-muted)', textAlign: 'left', borderBottom: '1px solid var(--border)', whiteSpace: 'nowrap' }}>
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} style={{ background: i % 2 === 0 ? 'transparent' : 'var(--surface)' }}>
              {shown.map((c) => {
                const v = row[c]
                return (
                  <td key={c} style={{ padding: '7px 12px', color: 'var(--text)', borderBottom: '1px solid var(--border)' }}>
                    {typeof v === 'number' ? (isFinite(v) ? v.toFixed(3) : '—') : v == null ? '—' : String(v)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}

const inputStyle: React.CSSProperties = {
  background: 'var(--surface-2)',
  border: '1px solid var(--border-2)',
  borderRadius: 5,
  color: 'var(--text)',
  padding: '5px 8px',
  fontSize: 12,
}

function btnStyle(disabled: boolean): React.CSSProperties {
  return {
    padding: '10px 0',
    background: disabled ? 'var(--surface-2)' : 'var(--accent)',
    color: disabled ? 'var(--text-dim)' : '#fff',
    border: 'none',
    borderRadius: 6,
    fontSize: 13,
    fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
    transition: 'background 0.15s',
  }
}
