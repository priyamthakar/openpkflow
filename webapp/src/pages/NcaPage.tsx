import { useCallback, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import Papa from 'papaparse'
import { TopBar } from '@/components/layout/TopBar'
import { LineChart } from 'lucide-react'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { ColumnMapper } from '@/components/shared/ColumnMapper'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { EmptyResults } from '@/components/shared/EmptyResults'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { PasteDataGrid, type PasteDataColumn, type PasteDataRow } from '@/components/shared/PasteDataGrid'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Button } from '@/components/ui/Button'
import { Select as UiSelect } from '@/components/ui/Select'
import { Skeleton } from '@/components/ui/Skeleton'
import { analyzeNca, downloadNcaReport } from '@/lib/api'
import { rowsToCsvFile } from '@/lib/gridCsv'
import { useRunShortcut } from '@/lib/useRunShortcut'
import type { NcaResponse } from '@/lib/types'

const AUC_METHODS = ['linear', 'log', 'linear_up_log_down'] as const
const BLQ_METHODS = ['none', 'drop', 'zero', 'half_lloq', 'lloq'] as const
const REQUIRED_COLUMNS = [
  { key: 'subject', label: 'Subject', default: 'subject' },
  { key: 'time', label: 'Time', default: 'time' },
  { key: 'conc', label: 'Concentration', default: 'conc' },
  { key: 'dose', label: 'Dose', default: 'dose' },
  { key: 'route', label: 'Route', default: 'route' },
]
const GRID_COLUMNS: PasteDataColumn[] = [
  { key: 'subject', label: 'Subject' },
  { key: 'time', label: 'Time', type: 'number' },
  { key: 'conc', label: 'Concentration', type: 'number' },
  { key: 'dose', label: 'Dose', type: 'number' },
  { key: 'route', label: 'Route' },
]
const PASTE_MAPPING: Record<string, string> = Object.fromEntries(
  GRID_COLUMNS.map((c) => [c.key, c.key]),
)
const EXAMPLE_NCA_ROWS: PasteDataRow[] = [
  { subject: 'S01', time: 0, conc: 0, dose: 320, route: 'oral' },
  { subject: 'S01', time: 1, conc: 2.4, dose: 320, route: 'oral' },
  { subject: 'S01', time: 2, conc: 5.6, dose: 320, route: 'oral' },
  { subject: 'S01', time: 4, conc: 6.8, dose: 320, route: 'oral' },
  { subject: 'S01', time: 8, conc: 4.1, dose: 320, route: 'oral' },
  { subject: 'S01', time: 12, conc: 2.2, dose: 320, route: 'oral' },
  { subject: 'S01', time: 16, conc: 1.2, dose: 320, route: 'oral' },
  { subject: 'S01', time: 24, conc: 0.4, dose: 320, route: 'oral' },
  { subject: 'S02', time: 0, conc: 0, dose: 320, route: 'oral' },
  { subject: 'S02', time: 1, conc: 1.9, dose: 320, route: 'oral' },
  { subject: 'S02', time: 2, conc: 4.8, dose: 320, route: 'oral' },
  { subject: 'S02', time: 4, conc: 6.1, dose: 320, route: 'oral' },
  { subject: 'S02', time: 8, conc: 3.7, dose: 320, route: 'oral' },
  { subject: 'S02', time: 12, conc: 2.0, dose: 320, route: 'oral' },
  { subject: 'S02', time: 16, conc: 1.1, dose: 320, route: 'oral' },
  { subject: 'S02', time: 24, conc: 0.35, dose: 320, route: 'oral' },
]

function downloadNcaTemplate() {
  const rows = [
    'subject,time,conc,dose,route',
    'S01,0,0,320,oral',
    'S01,1,2.4,320,oral',
    'S01,2,5.6,320,oral',
    'S01,4,6.8,320,oral',
    'S01,8,4.1,320,oral',
    'S01,12,2.2,320,oral',
    'S01,24,0.4,320,oral',
  ].join('\n')
  const blob = new Blob([rows], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'nca_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export default function NcaPage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [file, setFile] = useState<File | null>(null)
  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('upload')
  const [gridRows, setGridRows] = useState<PasteDataRow[]>(EXAMPLE_NCA_ROWS)
  const [headers, setHeaders] = useState<string[]>([])
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({})
  const [parseError, setParseError] = useState('')
  const [aucMethod, setAucMethod] = useState<string>('linear')
  const [blqMethod, setBlqMethod] = useState<string>('none')
  const [steadyState, setSteadyState] = useState(false)
  const [tau, setTau] = useState<number>(12)
  const [selectedSubject, setSelectedSubject] = useState<string>('')

  const gridFile = useMemo(() => rowsToCsvFile(GRID_COLUMNS, gridRows, 'nca_pasted_data.csv'), [gridRows])
  const activeFile = inputMode === 'paste' ? gridFile : file
  const activeColumns = inputMode === 'paste' ? PASTE_MAPPING : columnMapping

  const options = useMemo(
    () => ({
      auc_method: aucMethod,
      blq_method: blqMethod,
      steady_state: steadyState,
      tau: steadyState ? tau : undefined,
      columns: activeColumns,
    }),
    [aucMethod, blqMethod, steadyState, tau, activeColumns],
  )

  const [runSnapshot, setRunSnapshot] = useState<{
    options: typeof options
    fileKey: string
  } | null>(null)

  const mutation = useMutation<NcaResponse, Error>({
    mutationFn: () =>
      analyzeNca(activeFile!, options),
    onSuccess: (data) => {
      setRunSnapshot({
        options: { ...options, columns: { ...options.columns } },
        fileKey: `${activeFile?.name ?? ''}:${activeFile?.size ?? 0}:${activeFile?.lastModified ?? 0}`,
      })
      if (data.subjects.length > 0) setSelectedSubject(String(data.subjects[0].subject))
    },
  })

  const result = mutation.data
  const profile = result?.profiles.find((p) => p.subject === selectedSubject)
  const subjectRow = result?.subjects.find((r) => String(r.subject) === selectedSubject)

  const fileKey = `${activeFile?.name ?? ''}:${activeFile?.size ?? 0}:${activeFile?.lastModified ?? 0}`
  const resultsStale =
    Boolean(result) &&
    (runSnapshot === null ||
      runSnapshot.fileKey !== fileKey ||
      JSON.stringify(runSnapshot.options) !== JSON.stringify(options))

  const onFile = useCallback(
    (uploaded: File) => {
      setFile(uploaded)
      setHeaders([])
      setColumnMapping({})
      setParseError('')
      mutation.reset()
      parseCsvHeaders(uploaded)
        .then((fields) => {
          setHeaders(fields)
          setColumnMapping(buildInitialMapping(fields, REQUIRED_COLUMNS))
        })
        .catch((err) => setParseError((err as Error).message))
    },
    [mutation],
  )

  const canRun =
    Boolean(activeFile && (inputMode === 'paste' || headers.length > 0) && !mutation.isPending)

  useRunShortcut(mutation.mutate, canRun)

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Non-Compartmental Analysis"
        subtitle="Upload or paste PK data, configure options, and run NCA"
        onMenuClick={onMenuClick}
      />

      <AnalysisShell leftWide={inputMode === 'paste'} resultKey={result ? selectedSubject || 'nca' : null}>
        {/* Left panel */}
        <div>
          <div className="flex flex-col gap-4">
            {/* Step 1: Data Input */}
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                1. Data Input
              </h3>
              <SegmentedControl
                value={inputMode}
                onChange={(mode) => {
                  setInputMode(mode)
                  mutation.reset()
                  setSelectedSubject('')
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
                    onClick={downloadNcaTemplate}
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
                    mutation.reset()
                    setSelectedSubject('')
                  }}
                  filename="nca_pasted_data.csv"
                  hint="Paste concentration-time data from Excel or Prism. Headers are optional."
                />
              )}
              {parseError && <ErrorBanner message={parseError} className="mt-3" />}
            </section>

            {/* Step 2: Map Columns */}
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

            {/* Step 3: Options */}
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                {inputMode === 'upload' && headers.length > 0 ? '3.' : '2.'} Options
              </h3>
              <div className="space-y-2.5">
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">AUC Method</span>
                  <UiSelect
                    value={aucMethod}
                    onChange={(e) => setAucMethod(e.target.value)}
                    className="min-w-[150px]"
                  >
                    {AUC_METHODS.map((m) => (
                      <option key={m} value={m}>
                        {m.replace(/_/g, ' ')}
                      </option>
                    ))}
                  </UiSelect>
                </div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">BLQ Method</span>
                  <UiSelect
                    value={blqMethod}
                    onChange={(e) => setBlqMethod(e.target.value)}
                    className="min-w-[150px]"
                  >
                    {BLQ_METHODS.map((m) => (
                      <option key={m} value={m}>
                        {m}
                      </option>
                    ))}
                  </UiSelect>
                </div>
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={steadyState}
                    onChange={(e) => setSteadyState(e.target.checked)}
                    className="w-4 h-4 rounded border-border-2 text-accent focus:ring-accent/30"
                  />
                  <span className="text-sm font-semibold text-text">Steady State</span>
                </label>
                {steadyState && (
                  <div className="flex justify-between items-center gap-3">
                    <span className="text-sm font-semibold text-text shrink-0">Tau (h)</span>
                    <input
                      type="number"
                      value={tau}
                      onChange={(e) => setTau(Number(e.target.value))}
                      className="w-24 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                    />
                  </div>
                )}
              </div>
            </section>

            <Button onClick={() => mutation.mutate()} disabled={!canRun} loading={mutation.isPending} size="lg" className="w-full">
              {mutation.isPending ? 'Analyzing...' : 'Run NCA'}
            </Button>
          </div>
        </div>

        {/* Right panel */}
        <div className="flex-1 min-w-0 flex flex-col gap-5">
          {mutation.isError && (
            <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />
          )}

          {mutation.isPending && (
            <div className="space-y-5">
              <div className="flex gap-3 flex-wrap">
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
              </div>
              <Skeleton className="h-80 w-full rounded-sm" />
              <Skeleton className="h-48 w-full rounded-sm" />
            </div>
          )}

          {!result && !mutation.isPending && !mutation.isError && (
            <EmptyResults
              icon={LineChart}
              title="No results yet"
              description="Upload a CSV or paste your data, choose the AUC and BLQ methods, then run the analysis. Metrics, profiles, and the summary table will appear here."
            />
          )}

          {result && !mutation.isPending && (
            <>
              {resultsStale && (
                <div className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-warning text-sm">
                  <p className="font-semibold mb-1">Results are stale</p>
                  <p>
                    Options or input data changed after the last run. Re-run NCA before
                    downloading a report so the visible results and the report match.
                  </p>
                </div>
              )}
              {result.warnings.length > 0 && (
                <div className="rounded-sm border border-warning/20 bg-warning/5 p-3 text-warning text-sm">
                  <p className="font-semibold mb-1">Warnings</p>
                  {result.warnings.map((w, i) => (
                    <p key={i}>&bull; {w}</p>
                  ))}
                </div>
              )}

              <div className="flex items-center gap-3 flex-wrap">
                <label htmlFor="subject-select" className="text-sm font-semibold text-text">
                  Subject:
                </label>
                <UiSelect
                  id="subject-select"
                  value={selectedSubject}
                  onChange={(e) => setSelectedSubject(e.target.value)}
                  className="min-w-[120px]"
                >
                  {result.subjects.map((r) => (
                    <option key={String(r.subject)} value={String(r.subject)}>
                      {String(r.subject)}
                    </option>
                  ))}
                </UiSelect>
              </div>

              {subjectRow && (
                <div className="flex gap-3 flex-wrap">
                  <MetricCard label="AUClast" value={subjectRow.AUClast as number} />
                  <MetricCard label="AUCinf" value={subjectRow.AUCinf_obs as number} />
                  <MetricCard label="Cmax" value={subjectRow.Cmax as number} highlight />
                  <MetricCard label="Tmax" value={subjectRow.Tmax as number} unit="h" />
                  <MetricCard label="t1/2" value={subjectRow.half_life as number} unit="h" />
                  {subjectRow.CL_F != null && (
                    <MetricCard label="CL/F" value={subjectRow.CL_F as number} />
                  )}
                  {subjectRow.CL != null && (
                    <MetricCard label="CL" value={subjectRow.CL as number} />
                  )}
                </div>
              )}

              {profile && (
                <div className="bg-surface border border-border rounded-sm p-4 lg:p-5">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
                    Concentration-Time Profile for Subject {selectedSubject}
                  </h3>
                  <PKChart
                    series={[
                      {
                        name: `Subject ${selectedSubject}`,
                        times: profile.times,
                        concs: profile.concs,
                      },
                    ]}
                    xLabel="Time (h)"
                    yLabel="Concentration"
                    lambdaZ={profile.lambda_z_times.length > 0 ? profile : undefined}
                  />
                </div>
              )}

              <ResultTable columns={result.columns} rows={result.subjects} />
              {resultsStale ? (
                <p className="text-sm text-text-muted">
                  Report download disabled until you re-run with the current options.
                </p>
              ) : (
                <DownloadReportButton
                  onDownload={(fmt) =>
                    downloadNcaReport(activeFile!, runSnapshot!.options, fmt)
                  }
                />
              )}
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

function ResultTable({
  columns,
  rows,
}: {
  columns: string[]
  rows: Record<string, unknown>[]
}) {
  const KEY_COLS = [
    'subject', 'AUClast', 'AUCinf_obs', 'Cmax', 'Tmax',
    'half_life', 'CL_F', 'CL', 'Vz_F', 'Vz',
  ]
  const shown = KEY_COLS.filter((c) => columns.includes(c))
  if (shown.length === 0) return null
  return (
    <div className="rounded-sm border border-border">
      <div className="divide-y divide-border sm:hidden">
        {rows.map((row, i) => (
          <div key={i} className="p-3">
            <div className="mb-2 font-mono-ui text-xs font-semibold text-text-muted">
              Subject {formatTableValue(row.subject)}
            </div>
            <div className="grid grid-cols-2 gap-x-3 gap-y-2">
              {shown
                .filter((c) => c !== 'subject')
                .map((c) => (
                  <div key={c} className="min-w-0">
                    <div className="text-[11px] font-semibold uppercase text-text-muted">
                      {c}
                    </div>
                    <div className="truncate text-sm font-semibold text-text tabular-nums">
                      {formatTableValue(row[c])}
                    </div>
                  </div>
                ))}
            </div>
          </div>
        ))}
      </div>
      <div className="hidden overflow-x-auto sm:block">
        <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            {shown.map((c) => (
              <th
                key={c}
                className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border whitespace-nowrap font-semibold text-xs"
              >
                {c}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-transparent' : 'bg-surface'}>
              {shown.map((c) => {
                const v = row[c]
                return (
                  <td key={c} className="px-3 py-2 text-text border-b border-border tabular-nums">
                    {formatTableValue(v)}
                  </td>
                )
              })}
            </tr>
          ))}
        </tbody>
        </table>
      </div>
    </div>
  )
}

function formatTableValue(value: unknown) {
  if (typeof value === 'number') return isFinite(value) ? value.toFixed(3) : 'Not available'
  if (value == null) return 'Not available'
  return String(value)
}
