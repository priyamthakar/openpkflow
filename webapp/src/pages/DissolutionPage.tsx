import { useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { TopBar } from '@/components/layout/TopBar'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { fetchFormulations, compareFormulations, downloadDissolutionReport } from '@/lib/api'
import type { CompareResponse } from '@/lib/types'

export function DissolutionPage() {
  const [file, setFile] = useState<File | null>(null)
  const [formulations, setFormulations] = useState<string[]>([])
  const [reference, setReference] = useState('')
  const [test, setTest] = useState('')
  const [result, setResult] = useState<CompareResponse | null>(null)
  const [loadError, setLoadError] = useState('')

  const columns = {}

  async function onFile(f: File) {
    setFile(f)
    setLoadError('')
    try {
      const data = await fetchFormulations(f, columns)
      setFormulations(data.formulations)
      setReference(data.formulations[0] ?? '')
      setTest(data.formulations[1] ?? data.formulations[0] ?? '')
    } catch (e) {
      setLoadError(String((e as Error).message))
    }
  }

  const compareMutation = useMutation<CompareResponse, Error>({
    mutationFn: () => compareFormulations(file!, reference, test, columns),
    onSuccess: setResult,
  })

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar title="Dissolution Similarity" subtitle="f1/f2 comparison — FDA 1997 guidance" />

      <div style={{ flex: 1, overflowY: 'auto', padding: 28, display: 'flex', gap: 24 }}>
        {/* Left */}
        <div style={{ width: 300, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 16 }}>
          <section>
            <SL>1. Upload Data</SL>
            <FileDropzone onFile={onFile} />
            {loadError && <ErrorBanner message={loadError} />}
          </section>

          {formulations.length > 0 && (
            <section>
              <SL>2. Select Formulations</SL>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                <Lbl text="Reference">
                  <FmSelect value={reference} onChange={setReference} options={formulations} />
                </Lbl>
                <Lbl text="Test">
                  <FmSelect value={test} onChange={setTest} options={formulations} />
                </Lbl>
              </div>
            </section>
          )}

          <button
            onClick={() => compareMutation.mutate()}
            disabled={!file || !reference || !test || compareMutation.isPending}
            style={btnStyle(!file || !reference || !test || compareMutation.isPending)}
          >
            {compareMutation.isPending ? 'Comparing…' : 'Compare'}
          </button>
        </div>

        {/* Right */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {compareMutation.isError && <ErrorBanner message={compareMutation.error.message} />}

          {result && (
            <>
              {/* Verdict badge */}
              <div style={{ display: 'flex', alignItems: 'center', gap: 16 }}>
                <span
                  style={{
                    padding: '6px 14px', borderRadius: 20, fontSize: 13, fontWeight: 700,
                    background: result.similar ? 'rgba(61,214,140,0.12)' : 'rgba(229,83,75,0.12)',
                    color: result.similar ? 'var(--success)' : 'var(--danger)',
                    border: `1px solid ${result.similar ? 'rgba(61,214,140,0.3)' : 'rgba(229,83,75,0.3)'}`,
                  }}
                >
                  {result.similar ? '✓ SIMILAR (f2 ≥ 50)' : '✗ NOT SIMILAR (f2 < 50)'}
                </span>
              </div>

              {/* Metrics */}
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <MetricCard label="f1" value={result.f1_value.toFixed(2)} />
                <MetricCard label="f2" value={result.f2_value.toFixed(2)} highlight={result.similar} />
                <MetricCard label="Timepoints" value={result.n_timepoints} />
              </div>

              {/* Dissolution profile chart */}
              <div style={{ background: 'var(--surface)', border: '1px solid var(--border)', borderRadius: 'var(--radius)', padding: 20 }}>
                <h3 style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 12, textTransform: 'uppercase', letterSpacing: '0.06em' }}>
                  Dissolution Profiles
                </h3>
                <PKChart
                  series={[
                    { name: result.reference_label, times: result.time_points, concs: result.reference_mean, color: '#5e6ad2' },
                    { name: result.test_label, times: result.time_points, concs: result.test_mean, color: '#3dd68c', dashed: true },
                  ]}
                  xLabel="Time (min)"
                  yLabel="% Dissolved"
                  thresholdY={85}
                  thresholdLabel="85% threshold"
                />
              </div>

              {/* Warnings */}
              {result.warnings.length > 0 && (
                <div style={{ padding: '10px 14px', background: 'rgba(240,167,49,0.06)', border: '1px solid rgba(240,167,49,0.2)', borderRadius: 'var(--radius)', fontSize: 12, color: 'var(--warning)' }}>
                  <p style={{ fontWeight: 600, marginBottom: 4 }}>Regulatory Warnings</p>
                  {result.warnings.map((w, i) => <p key={i}>• {w}</p>)}
                </div>
              )}

              <DownloadReportButton
                onDownload={(fmt) => downloadDissolutionReport(file!, reference, test, columns, fmt)}
              />
              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function SL({ children }: { children: string }) {
  return <p style={{ fontSize: 11, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: 8 }}>{children}</p>
}
function Lbl({ text, children }: { text: string; children: React.ReactNode }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', gap: 8 }}>
      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{text}</span>
      {children}
    </div>
  )
}
function FmSelect({ value, onChange, options }: { value: string; onChange: (v: string) => void; options: string[] }) {
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)}
      style={{ background: 'var(--surface-2)', border: '1px solid var(--border-2)', borderRadius: 5, color: 'var(--text)', padding: '5px 8px', fontSize: 12, minWidth: 130 }}>
      {options.map((o) => <option key={o}>{o}</option>)}
    </select>
  )
}
function btnStyle(disabled: boolean): React.CSSProperties {
  return {
    padding: '10px 0',
    background: disabled ? 'var(--surface-2)' : 'var(--accent)',
    color: disabled ? 'var(--text-dim)' : '#fff',
    border: 'none', borderRadius: 6, fontSize: 13, fontWeight: 600,
    cursor: disabled ? 'not-allowed' : 'pointer',
  }
}
