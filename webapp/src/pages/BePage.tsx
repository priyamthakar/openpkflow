import { useCallback, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import Papa from 'papaparse'
import { TopBar } from '@/components/layout/TopBar'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { ColumnMapper } from '@/components/shared/ColumnMapper'
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
import { Skeleton } from '@/components/ui/Skeleton'
import { analyzeBe, downloadBeReport } from '@/lib/api'
import { rowsToCsvFile } from '@/lib/gridCsv'
import type { BeResponse } from '@/lib/types'

const PARAMETERS = ['AUCinf', 'AUClast', 'Cmax'] as const

const REQUIRED_COLUMNS = [
  { key: 'subject_col', label: 'Subject', default: 'subject' },
  { key: 'reference_col', label: 'Reference', default: 'reference' },
  { key: 'test_col', label: 'Test', default: 'test' },
]
const OPTIONAL_SEQUENCE_COL = { key: 'sequence_col', label: 'Sequence', default: 'sequence' }

const GRID_COLUMNS: PasteDataColumn[] = [
  { key: 'subject', label: 'Subject' },
  { key: 'sequence', label: 'Sequence' },
  { key: 'reference', label: 'Reference', type: 'number' },
  { key: 'test', label: 'Test', type: 'number' },
]
const PASTE_MAPPING: Record<string, string> = {
  subject_col: 'subject',
  reference_col: 'reference',
  test_col: 'test',
  sequence_col: 'sequence',
}
const EXAMPLE_BE_ROWS: PasteDataRow[] = [
  { subject: 'S01', sequence: 'RT', reference: 100.2, test: 96.4 },
  { subject: 'S02', sequence: 'RT', reference: 112.5, test: 108.1 },
  { subject: 'S03', sequence: 'TR', reference: 95.8, test: 91.3 },
  { subject: 'S04', sequence: 'TR', reference: 108.0, test: 102.7 },
  { subject: 'S05', sequence: 'RT', reference: 103.4, test: 99.8 },
  { subject: 'S06', sequence: 'TR', reference: 97.6, test: 94.1 },
]

function downloadTemplateCsv() {
  const rows = [
    'subject,sequence,reference,test',
    'S01,RT,100.2,96.4',
    'S02,RT,112.5,108.1',
    'S03,TR,95.8,91.3',
    'S04,TR,108.0,102.7',
  ].join('\n')
  const blob = new Blob([rows], { type: 'text/csv' })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = 'be_template.csv'
  a.click()
  URL.revokeObjectURL(url)
}

export default function BePage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [file, setFile] = useState<File | null>(null)
  const [inputMode, setInputMode] = useState<'upload' | 'paste'>('upload')
  const [gridRows, setGridRows] = useState<PasteDataRow[]>(EXAMPLE_BE_ROWS)
  const [headers, setHeaders] = useState<string[]>([])
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({})
  const [parseError, setParseError] = useState('')
  const [parameter, setParameter] = useState<string>('AUCinf')
  const [beLower, setBeLower] = useState<number>(0.80)
  const [beUpper, setBeUpper] = useState<number>(1.25)
  const [alpha, setAlpha] = useState<number>(0.05)
  const [hasSequence, setHasSequence] = useState(true)

  const gridFile = useMemo(
    () => rowsToCsvFile(GRID_COLUMNS, gridRows, 'be_pasted_data.csv'),
    [gridRows],
  )
  const activeFile = inputMode === 'paste' ? gridFile : file
  const activeColumns = inputMode === 'paste' ? PASTE_MAPPING : columnMapping

  const buildOptions = useCallback(
    () => ({
      parameter,
      reference_col: activeColumns.reference_col ?? 'reference',
      test_col: activeColumns.test_col ?? 'test',
      subject_col: activeColumns.subject_col ?? 'subject',
      sequence_col: hasSequence ? (activeColumns.sequence_col ?? 'sequence') : null,
      be_lower: beLower,
      be_upper: beUpper,
      alpha,
      columns: {},
    }),
    [parameter, activeColumns, hasSequence, beLower, beUpper, alpha],
  )

  const mutation = useMutation<BeResponse, Error>({
    mutationFn: () => analyzeBe(activeFile!, buildOptions()),
  })

  const result = mutation.data

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
          const allCols = [
            ...REQUIRED_COLUMNS,
            ...(hasSequence ? [OPTIONAL_SEQUENCE_COL] : []),
          ]
          setColumnMapping(buildInitialMapping(fields, allCols))
        })
        .catch((err) => setParseError((err as Error).message))
    },
    [mutation, hasSequence],
  )

  const canRun = Boolean(activeFile && !mutation.isPending)

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Bioequivalence"
        subtitle="2x2 crossover TOST analysis with 80-125% acceptance limits"
        onMenuClick={onMenuClick}
      />

      <AnalysisShell leftWide={inputMode === 'paste'} resultKey={Boolean(result)}>
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
                    onClick={downloadTemplateCsv}
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
                  }}
                  filename="be_pasted_data.csv"
                  hint="One row per subject. Sequence column: RT or TR (optional)."
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
                  required={[
                    ...REQUIRED_COLUMNS,
                    ...(hasSequence ? [OPTIONAL_SEQUENCE_COL] : []),
                  ]}
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
                  <span className="text-sm font-semibold text-text shrink-0">Parameter</span>
                  <UiSelect
                    value={parameter}
                    onChange={(e) => setParameter(e.target.value)}
                    className="min-w-[130px]"
                  >
                    {PARAMETERS.map((p) => (
                      <option key={p} value={p}>{p}</option>
                    ))}
                  </UiSelect>
                </div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">Lower limit</span>
                  <input
                    type="number"
                    value={beLower}
                    step={0.01}
                    min={0.5}
                    max={1}
                    onChange={(e) => setBeLower(Number(e.target.value))}
                    className="w-24 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                  />
                </div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">Upper limit</span>
                  <input
                    type="number"
                    value={beUpper}
                    step={0.01}
                    min={1}
                    max={2}
                    onChange={(e) => setBeUpper(Number(e.target.value))}
                    className="w-24 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                  />
                </div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">Alpha</span>
                  <input
                    type="number"
                    value={alpha}
                    step={0.01}
                    min={0.01}
                    max={0.1}
                    onChange={(e) => setAlpha(Number(e.target.value))}
                    className="w-24 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                  />
                </div>
                <label className="flex items-center gap-2.5 cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hasSequence}
                    onChange={(e) => setHasSequence(e.target.checked)}
                    className="w-4 h-4 rounded border-border-2 text-accent focus:ring-accent/30"
                  />
                  <span className="text-sm font-semibold text-text">Dataset has sequence column (RT/TR)</span>
                </label>
              </div>
            </section>

            <Button
              onClick={() => mutation.mutate()}
              disabled={!canRun}
              loading={mutation.isPending}
              size="lg"
              className="w-full"
            >
              {mutation.isPending ? 'Analyzing...' : 'Run BE Analysis'}
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
              <Skeleton className="h-16 w-full rounded-sm" />
              <div className="flex gap-3 flex-wrap">
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
              </div>
              <Skeleton className="h-48 w-full rounded-sm" />
            </div>
          )}

          {result && !mutation.isPending && (
            <>
              {/* Verdict banner */}
              <div
                className={`rounded-sm border px-5 py-4 flex items-center gap-4 ${
                  result.bioequivalent
                    ? 'bg-success/5 border-success/20'
                    : 'bg-danger/5 border-danger/20'
                }`}
              >
                <Badge variant={result.bioequivalent ? 'success' : 'danger'} >
                  {result.bioequivalent ? 'BIOEQUIVALENT' : 'NOT BIOEQUIVALENT'}
                </Badge>
                <span className="text-sm text-text-muted">
                  {result.parameter} / 90% CI [{result.gmr_lower_90ci.toFixed(4)},{' '}
                  {result.gmr_upper_90ci.toFixed(4)}] vs limits [{result.be_lower.toFixed(2)},{' '}
                  {result.be_upper.toFixed(2)}]
                </span>
              </div>

              {/* Metric cards */}
              <div className="flex gap-3 flex-wrap">
                <MetricCard label="GMR (T/R)" value={result.gmr} highlight />
                <MetricCard label="90% CI lower" value={result.gmr_lower_90ci} />
                <MetricCard label="90% CI upper" value={result.gmr_upper_90ci} />
                <MetricCard label="CV% intra" value={result.cv_intra_pct} unit="%" />
                <MetricCard label="n subjects" value={result.n} />
              </div>

              {/* CI bar visualization */}
              <CiBar
                lower={result.gmr_lower_90ci}
                upper={result.gmr_upper_90ci}
                gmr={result.gmr}
                limitLower={result.be_lower}
                limitUpper={result.be_upper}
              />

              {/* Subject table */}
              <SubjectTable rows={result.subjects} parameter={result.parameter} />

              <DownloadReportButton
                formats={['html', 'markdown']}
                onDownload={(fmt) => downloadBeReport(activeFile!, buildOptions(), fmt)}
              />
              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </div>
      </AnalysisShell>
    </div>
  )
}

function CiBar({
  lower,
  upper,
  gmr,
  limitLower,
  limitUpper,
}: {
  lower: number
  upper: number
  gmr: number
  limitLower: number
  limitUpper: number
}) {
  const viewMin = 0.6
  const viewMax = 1.4
  const range = viewMax - viewMin
  const pct = (v: number) => `${((v - viewMin) / range) * 100}%`

  const withinLimits = lower >= limitLower && upper <= limitUpper

  return (
    <div className="bg-surface border border-border rounded-sm p-4 lg:p-5">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-4">
        90% Confidence Interval
      </h3>
      <div className="relative h-10 rounded-sm overflow-hidden bg-surface-2">
        {/* Acceptance zone */}
        <div
          className="absolute top-0 bottom-0 bg-success/15 border-x border-success/30"
          style={{ left: pct(limitLower), width: `calc(${pct(limitUpper)} - ${pct(limitLower)})` }}
        />
        {/* CI bar */}
        <div
          className={`absolute top-[30%] bottom-[30%] rounded-sm ${withinLimits ? 'bg-success' : 'bg-danger'}`}
          style={{ left: pct(lower), width: `calc(${pct(upper)} - ${pct(lower)})` }}
        />
        {/* GMR tick */}
        <div
          className="absolute top-0 bottom-0 w-0.5 bg-text"
          style={{ left: pct(gmr) }}
        />
      </div>
      <div className="flex justify-between text-[11px] text-text-dim mt-1">
        <span>{viewMin.toFixed(1)}</span>
        <span className="text-success text-xs">{limitLower} to {limitUpper} acceptance limits</span>
        <span>{viewMax.toFixed(1)}</span>
      </div>
    </div>
  )
}

function SubjectTable({ rows, parameter }: { rows: BeResponse['subjects']; parameter: string }) {
  const hasSequence = rows.some((r) => r.sequence != null)
  return (
    <div className="overflow-x-auto rounded-sm border border-border">
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border whitespace-nowrap font-semibold text-xs">Subject</th>
            {hasSequence && <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border whitespace-nowrap font-semibold text-xs">Sequence</th>}
            <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border whitespace-nowrap font-semibold text-xs">Reference ({parameter})</th>
            <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border whitespace-nowrap font-semibold text-xs">Test ({parameter})</th>
            <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border whitespace-nowrap font-semibold text-xs">Ratio (T/R)</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className={i % 2 === 0 ? 'bg-transparent' : 'bg-surface'}>
              <td className="px-3 py-2 text-text border-b border-border">{row.subject}</td>
              {hasSequence && <td className="px-3 py-2 text-text border-b border-border">{row.sequence ?? 'Not available'}</td>}
              <td className="px-3 py-2 text-text border-b border-border tabular-nums">{row.reference.toFixed(3)}</td>
              <td className="px-3 py-2 text-text border-b border-border tabular-nums">{row.test.toFixed(3)}</td>
              <td className="px-3 py-2 text-text border-b border-border tabular-nums">{row.ratio.toFixed(4)}</td>
            </tr>
          ))}
        </tbody>
      </table>
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
