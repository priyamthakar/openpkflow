import { useCallback, useEffect, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import Papa from 'papaparse'
import { TopBar } from '@/components/layout/TopBar'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { ColumnMapper } from '@/components/shared/ColumnMapper'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { PasteDataGrid, type PasteDataColumn, type PasteDataRow } from '@/components/shared/PasteDataGrid'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select as UiSelect } from '@/components/ui/Select'
import { fetchFormulations, compareFormulations, downloadDissolutionReport } from '@/lib/api'
import { rowsToCsvFile } from '@/lib/gridCsv'
import type { CompareResponse } from '@/lib/types'

const REQUIRED_COLUMNS = [
  { key: 'formulation', label: 'Formulation', default: 'formulation' },
  { key: 'batch', label: 'Batch', default: 'batch' },
  { key: 'time', label: 'Time', default: 'time' },
  { key: 'percent_released', label: '% Released', default: 'percent_released' },
]
const GRID_COLUMNS: PasteDataColumn[] = [
  { key: 'formulation', label: 'Formulation' },
  { key: 'batch', label: 'Batch' },
  { key: 'time', label: 'Time', type: 'number' },
  { key: 'percent_released', label: '% Released', type: 'number' },
]
const PASTE_MAPPING: Record<string, string> = Object.fromEntries(
  GRID_COLUMNS.map((c) => [c.key, c.key]),
)
const EXAMPLE_DISSOLUTION_ROWS: PasteDataRow[] = [
  { formulation: 'Reference', batch: 'R1', time: 5, percent_released: 28 },
  { formulation: 'Reference', batch: 'R1', time: 10, percent_released: 48 },
  { formulation: 'Reference', batch: 'R1', time: 15, percent_released: 67 },
  { formulation: 'Reference', batch: 'R1', time: 30, percent_released: 91 },
  { formulation: 'Reference', batch: 'R2', time: 5, percent_released: 30 },
  { formulation: 'Reference', batch: 'R2', time: 10, percent_released: 50 },
  { formulation: 'Reference', batch: 'R2', time: 15, percent_released: 69 },
  { formulation: 'Reference', batch: 'R2', time: 30, percent_released: 93 },
  { formulation: 'Test', batch: 'T1', time: 5, percent_released: 26 },
  { formulation: 'Test', batch: 'T1', time: 10, percent_released: 47 },
  { formulation: 'Test', batch: 'T1', time: 15, percent_released: 66 },
  { formulation: 'Test', batch: 'T1', time: 30, percent_released: 90 },
  { formulation: 'Test', batch: 'T2', time: 5, percent_released: 27 },
  { formulation: 'Test', batch: 'T2', time: 10, percent_released: 49 },
  { formulation: 'Test', batch: 'T2', time: 15, percent_released: 68 },
  { formulation: 'Test', batch: 'T2', time: 30, percent_released: 92 },
]

function downloadDissolutionTemplate() {
  const rows = [
    'formulation,batch,time,percent_released',
    'Reference,R1,5,28',
    'Reference,R1,10,48',
    'Reference,R1,15,67',
    'Reference,R1,30,91',
    'Test,T1,5,26',
    'Test,T1,10,47',
    'Test,T1,15,66',
    'Test,T1,30,90',
  ].join('\n')
  const blob = new Blob([rows], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'dissolution_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export default function DissolutionPage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [file, setFile] = useState<File | null>(null)
  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('upload')
  const [gridRows, setGridRows] = useState<PasteDataRow[]>(EXAMPLE_DISSOLUTION_ROWS)
  const [headers, setHeaders] = useState<string[]>([])
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({})
  const [formulations, setFormulations] = useState<string[]>([])
  const [reference, setReference] = useState('')
  const [test, setTest] = useState('')
  const [result, setResult] = useState<CompareResponse | null>(null)
  const [loadError, setLoadError] = useState('')

  const gridFile = useMemo(() => rowsToCsvFile(GRID_COLUMNS, gridRows, 'dissolution_pasted_data.csv'), [gridRows])
  const activeFile = inputMode === 'paste' ? gridFile : file
  const columns = useMemo(() => (inputMode === 'paste' ? PASTE_MAPPING : columnMapping), [inputMode, columnMapping])

  const onFile = useCallback((f: File) => {
    setFile(f)
    setHeaders([])
    setColumnMapping({})
    setFormulations([])
    setReference('')
    setTest('')
    setResult(null)
    setLoadError('')
    parseCsvHeaders(f)
      .then((fields) => {
        setHeaders(fields)
        setColumnMapping(buildInitialMapping(fields, REQUIRED_COLUMNS))
      })
      .catch((err) => setLoadError((err as Error).message))
  }, [])

  useEffect(() => {
    if (!activeFile || (inputMode === 'upload' && headers.length === 0) || Object.keys(columns).length === 0) return
    let ignore = false
    fetchFormulations(activeFile, columns)
      .then((data) => {
        if (ignore) return
        setLoadError('')
        setFormulations(data.formulations)
        setReference(data.formulations[0] ?? '')
        setTest(data.formulations[1] ?? data.formulations[0] ?? '')
      })
      .catch((e) => {
        if (!ignore) setLoadError(String((e as Error).message))
      })
    return () => {
      ignore = true
    }
  }, [activeFile, headers.length, inputMode, columns])

  const compareMutation = useMutation<CompareResponse, Error>({
    mutationFn: () => compareFormulations(activeFile!, reference, test, columns),
    onSuccess: setResult,
  })

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Dissolution Similarity"
        subtitle="Upload or paste dissolution data for f1/f2 comparison"
        onMenuClick={onMenuClick}
      />

      <AnalysisShell leftWide={inputMode === 'paste'} resultKey={Boolean(result)}>
        {/* Left panel */}
        <div>
          <div className="flex flex-col gap-4">
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                1. Data Input
              </h3>
              <SegmentedControl
                value={inputMode}
                onChange={(mode) => {
                  setInputMode(mode)
                  setResult(null)
                  compareMutation.reset()
                }}
                options={[
                  { value: 'upload', label: 'Upload CSV' },
                  { value: 'paste', label: 'Paste table' },
                ]}
                className="mb-3"
              />
              {inputMode === 'upload' ? (
                <>
                  <FileDropzone onFile={onFile} />
                  <button
                    type="button"
                    onClick={downloadDissolutionTemplate}
                    className="mt-2 text-xs text-text-muted hover:text-text underline underline-offset-2 transition-colors"
                  >
                    Download template CSV
                  </button>
                </>
              ) : (
                <PasteDataGrid
                  columns={GRID_COLUMNS}
                  rows={gridRows}
                  onChange={(rows) => {
                    setGridRows(rows)
                    setResult(null)
                    compareMutation.reset()
                  }}
                  filename="dissolution_pasted_data.csv"
                  hint="Paste formulation, batch, time, and percent released data from Excel or Prism."
                />
              )}
              {loadError && <ErrorBanner message={loadError} className="mt-3" />}
            </section>

            {inputMode === 'upload' && headers.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                  2. Map Columns
                </h3>
                <ColumnMapper
                  headers={headers}
                  required={REQUIRED_COLUMNS}
                  value={columnMapping}
                  onChange={setColumnMapping}
                />
              </section>
            )}

            {formulations.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                  {inputMode === 'upload' && headers.length > 0 ? '3.' : '2.'} Select Formulations
                </h3>
                <div className="space-y-2.5">
                  <div className="flex justify-between items-center gap-3">
                    <span className="text-sm font-semibold text-text shrink-0">Reference</span>
                    <UiSelect value={reference} onChange={(e) => setReference(e.target.value)} className="min-w-[150px]">
                      {formulations.map((f) => (
                        <option key={f} value={f}>{f}</option>
                      ))}
                    </UiSelect>
                  </div>
                  <div className="flex justify-between items-center gap-3">
                    <span className="text-sm font-semibold text-text shrink-0">Test</span>
                    <UiSelect value={test} onChange={(e) => setTest(e.target.value)} className="min-w-[150px]">
                      {formulations.map((f) => (
                        <option key={f} value={f}>{f}</option>
                      ))}
                    </UiSelect>
                  </div>
                </div>
              </section>
            )}

            <Button
              onClick={() => compareMutation.mutate()}
              disabled={
                !activeFile ||
                (inputMode === 'upload' && headers.length === 0) ||
                !reference ||
                !test ||
                compareMutation.isPending
              }
              loading={compareMutation.isPending}
              size="lg"
              className="w-full"
            >
              {compareMutation.isPending ? 'Comparing...' : 'Compare'}
            </Button>
          </div>
        </div>

        {/* Right panel */}
        <div className="flex-1 min-w-0 flex flex-col gap-5">
          {compareMutation.isError && (
            <ErrorBanner message={compareMutation.error.message} onDismiss={() => compareMutation.reset()} />
          )}

          {result && !compareMutation.isPending && (
            <>
              <div className="flex items-center gap-4 flex-wrap">
                <Badge variant={result.similar ? 'success' : 'danger'}>
                  {result.similar ? 'Similar: f2 >= 50' : 'Not similar: f2 < 50'}
                </Badge>
              </div>

              <div className="flex gap-3 flex-wrap">
                <MetricCard label="f1" value={result.f1_value} />
                <MetricCard label="f2" value={result.f2_value} highlight={result.similar} />
                <MetricCard label="Timepoints" value={result.n_timepoints} />
              </div>

              <div className="bg-surface border border-border rounded-sm p-4 lg:p-5">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
                  Dissolution Profiles
                </h3>
                <PKChart
                  series={[
                    {
                      name: result.reference_label,
                      times: result.time_points,
                      concs: result.reference_mean,
                      color: '#5e6ad2',
                    },
                    {
                      name: result.test_label,
                      times: result.time_points,
                      concs: result.test_mean,
                      color: '#3dd68c',
                      dashed: true,
                    },
                  ]}
                  xLabel="Time (min)"
                  yLabel="% Dissolved"
                  thresholdY={85}
                  thresholdLabel="85% threshold"
                />
              </div>

              {result.warnings.length > 0 && (
                <div className="rounded-sm border border-warning/20 bg-warning/5 p-3 text-warning text-sm">
                  <p className="font-semibold mb-1">Regulatory Warnings</p>
                  {result.warnings.map((w, i) => (
                    <p key={i}>&bull; {w}</p>
                  ))}
                </div>
              )}

              <DownloadReportButton
                onDownload={(fmt) =>
                  downloadDissolutionReport(activeFile!, reference, test, columns, fmt)
                }
              />
              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </div>
      </AnalysisShell>
    </div>
  )
}

function buildInitialMapping(
  headers: string[],
  required: { key: string; default: string }[],
): Record<string, string> {
  const fallback = headers[0] ?? ''
  return required.reduce<Record<string, string>>((acc, col) => {
    const exact = headers.find((h) => h.toLowerCase() === col.default.toLowerCase())
    acc[col.key] = exact ?? fallback
    return acc
  }, {})
}

function parseCsvHeaders(file: File): Promise<string[]> {
  return new Promise((resolve, reject) => {
    Papa.parse<Record<string, string>>(file, {
      preview: 1,
      header: true,
      complete: (results) => {
        const fields = results.meta.fields?.filter(Boolean) ?? []
        if (fields.length === 0) {
          reject(new Error('No CSV headers found.'))
          return
        }
        resolve(fields)
      },
      error: (error) => reject(error),
    })
  })
}
