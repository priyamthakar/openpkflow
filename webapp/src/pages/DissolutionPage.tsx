import { useCallback, useEffect, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import Papa from 'papaparse'
import { Waves } from 'lucide-react'
import { TopBar } from '@/components/layout/TopBar'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { ColumnMapper } from '@/components/shared/ColumnMapper'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { EmptyResults } from '@/components/shared/EmptyResults'
import { DissolutionWorkbench } from '@/components/dissolution/DissolutionWorkbench'
import { PasteDataGrid, type PasteDataColumn, type PasteDataRow } from '@/components/shared/PasteDataGrid'
import { SegmentedControl } from '@/components/ui/SegmentedControl'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select as UiSelect } from '@/components/ui/Select'
import {
  fetchFormulations,
  compareFormulations,
  downloadDissolutionReport,
  analyzeMultiMedia,
  downloadMultiMediaReport,
} from '@/lib/api'
import { useRunShortcut } from '@/lib/useRunShortcut'
import { rowsToCsvFile } from '@/lib/gridCsv'
import type { CompareResponse, DissolutionRowPayload, MultiMediaResponse } from '@/lib/types'

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

type MediaSlot = { name: string; rows: PasteDataRow[] }

function buildExampleMediaRows(offset = 0): PasteDataRow[] {
  const times = [5, 10, 15, 20, 30, 45, 60]
  const ref = [5, 15, 30, 45, 60, 80, 95]
  const tst = [6 + offset, 16 + offset, 31, 44, 58, 78, 93]
  const rows: PasteDataRow[] = []
  for (let i = 0; i < times.length; i++) {
    rows.push({ formulation: 'reference', batch: 'R1', time: times[i], percent_released: ref[i] })
    rows.push({ formulation: 'test', batch: 'T1', time: times[i], percent_released: tst[i] })
  }
  return rows
}

const EXAMPLE_MEDIA: MediaSlot[] = [
  { name: 'pH 1.2', rows: buildExampleMediaRows(0) },
  { name: 'pH 4.5', rows: buildExampleMediaRows(0) },
  { name: 'pH 6.8', rows: buildExampleMediaRows(0) },
]

function gridRowsToPayload(rows: PasteDataRow[]): DissolutionRowPayload[] {
  return rows
    .filter(
      (r) =>
        String(r.formulation ?? '').trim() !== '' &&
        String(r.time ?? '').trim() !== '' &&
        String(r.percent_released ?? '').trim() !== '',
    )
    .map((r) => ({
      formulation: String(r.formulation),
      batch: String(r.batch ?? '1'),
      time: Number(r.time),
      percent_released: Number(r.percent_released),
    }))
}

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
  const [pageTab, setPageTab] = useState<'single' | 'multi' | 'workbench'>('single')
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

  // Multi-media state
  const [mediaSlots, setMediaSlots] = useState<MediaSlot[]>(EXAMPLE_MEDIA)
  const [mmReference, setMmReference] = useState('reference')
  const [mmTest, setMmTest] = useState('test')
  const [activeMediumIdx, setActiveMediumIdx] = useState(0)

  const gridFile = useMemo(() => rowsToCsvFile(GRID_COLUMNS, gridRows, 'dissolution_pasted_data.csv'), [gridRows])
  const activeFile = inputMode === 'paste' ? gridFile : file
  const columns = useMemo(() => (inputMode === 'paste' ? PASTE_MAPPING : columnMapping), [inputMode, columnMapping])
  const pastedFormulations = useMemo(() => {
    const labels = gridRows
      .map((row) => String(row.formulation ?? '').trim())
      .filter(Boolean)
    return Array.from(new Set(labels))
  }, [gridRows])

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
    if (inputMode === 'paste') return
    if (!activeFile || headers.length === 0 || Object.keys(columns).length === 0) return
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

  const compareMutation = useMutation<
    CompareResponse,
    Error,
    { file: File; reference: string; test: string; columns: Record<string, string> }
  >({
    mutationFn: (payload) => (
      compareFormulations(payload.file, payload.reference, payload.test, payload.columns)
    ),
    onSuccess: setResult,
  })

  const selectableFormulations = inputMode === 'paste' ? pastedFormulations : formulations
  const selectedReference = selectableFormulations.includes(reference)
    ? reference
    : (selectableFormulations[0] ?? '')
  const selectedTest = selectableFormulations.includes(test)
    ? test
    : (selectableFormulations[1] ?? selectableFormulations[0] ?? '')

  const runCompare = () => {
    if (!activeFile || !selectedReference || !selectedTest) return
    compareMutation.mutate({
      file: activeFile,
      reference: selectedReference,
      test: selectedTest,
      columns,
    })
  }

  const canRunSingle =
    Boolean(activeFile) &&
    (inputMode !== 'upload' || headers.length > 0) &&
    Boolean(selectedReference) &&
    Boolean(selectedTest) &&
    !compareMutation.isPending

  useRunShortcut(runCompare, pageTab === 'single' && canRunSingle)

  const multiMediaMutation = useMutation<MultiMediaResponse, Error>({
    mutationFn: () =>
      analyzeMultiMedia({
        media: mediaSlots.map((m) => ({
          name: m.name,
          rows: gridRowsToPayload(m.rows),
        })),
        reference_label: mmReference,
        test_label: mmTest,
      }),
  })
  const mmResult = multiMediaMutation.data

  const canRunMulti = mediaSlots.length >= 2 && !multiMediaMutation.isPending
  useRunShortcut(multiMediaMutation.mutate, pageTab === 'multi' && canRunMulti)

  const mmReq = useMemo(
    () => ({
      media: mediaSlots.map((m) => ({
        name: m.name,
        rows: gridRowsToPayload(m.rows),
      })),
      reference_label: mmReference,
      test_label: mmTest,
    }),
    [mediaSlots, mmReference, mmTest],
  )

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="Dissolution"
        subtitle="Similarity, multi-media, and auditable advanced analysis"
        onMenuClick={onMenuClick}
      />

      <div className="px-4 pt-3 lg:px-6">
        <SegmentedControl
          value={pageTab}
          onChange={setPageTab}
          options={[
            { value: 'single', label: 'Single medium' },
            { value: 'multi', label: 'Multi-media' },
            { value: 'workbench', label: 'Advanced workbench' },
          ]}
        />
      </div>

      {pageTab === 'multi' ? (
        <AnalysisShell leftWide resultKey={Boolean(mmResult)}>
          <div>
            <div className="flex flex-col gap-4">
              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                  1. Media panels
                </h3>
                <div className="flex flex-wrap gap-2 mb-3">
                  {mediaSlots.map((m, i) => (
                    <button
                      key={i}
                      type="button"
                      onClick={() => setActiveMediumIdx(i)}
                      className={`px-3 py-1.5 text-sm rounded-sm border transition-colors ${
                        activeMediumIdx === i
                          ? 'border-accent bg-accent/10 text-text font-semibold'
                          : 'border-border bg-surface-2 text-text-muted hover:text-text'
                      }`}
                    >
                      {m.name || `Medium ${i + 1}`}
                    </button>
                  ))}
                  {mediaSlots.length < 6 && (
                    <button
                      type="button"
                      onClick={() => {
                        setMediaSlots((prev) => [
                          ...prev,
                          { name: `Medium ${prev.length + 1}`, rows: buildExampleMediaRows() },
                        ])
                        setActiveMediumIdx(mediaSlots.length)
                        multiMediaMutation.reset()
                      }}
                      className="px-3 py-1.5 text-sm rounded-sm border border-dashed border-border-2 text-text-muted hover:text-text"
                    >
                      + Add medium
                    </button>
                  )}
                </div>
                {mediaSlots[activeMediumIdx] && (
                  <>
                    <div className="flex justify-between items-center gap-3 mb-2">
                      <span className="text-sm font-semibold text-text shrink-0">Medium name</span>
                      <input
                        type="text"
                        value={mediaSlots[activeMediumIdx].name}
                        onChange={(e) => {
                          const name = e.target.value
                          setMediaSlots((prev) =>
                            prev.map((m, i) => (i === activeMediumIdx ? { ...m, name } : m)),
                          )
                          multiMediaMutation.reset()
                        }}
                        className="w-40 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                      />
                    </div>
                    <PasteDataGrid
                      columns={GRID_COLUMNS}
                      rows={mediaSlots[activeMediumIdx].rows}
                      onChange={(rows) => {
                        setMediaSlots((prev) =>
                          prev.map((m, i) => (i === activeMediumIdx ? { ...m, rows } : m)),
                        )
                        multiMediaMutation.reset()
                      }}
                      filename={`${mediaSlots[activeMediumIdx].name || 'medium'}.csv`}
                      hint="Paste dissolution data for this medium (formulation, batch, time, % released)."
                    />
                    {mediaSlots.length > 2 && (
                      <button
                        type="button"
                        onClick={() => {
                          setMediaSlots((prev) => prev.filter((_, i) => i !== activeMediumIdx))
                          setActiveMediumIdx(0)
                          multiMediaMutation.reset()
                        }}
                        className="mt-2 text-xs text-danger hover:underline"
                      >
                        Remove this medium
                      </button>
                    )}
                  </>
                )}
              </section>

              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                  2. Formulations
                </h3>
                <div className="space-y-2.5">
                  <div className="flex justify-between items-center gap-3">
                    <span className="text-sm font-semibold text-text shrink-0">Reference label</span>
                    <input
                      type="text"
                      value={mmReference}
                      onChange={(e) => {
                        setMmReference(e.target.value)
                        multiMediaMutation.reset()
                      }}
                      className="w-40 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                    />
                  </div>
                  <div className="flex justify-between items-center gap-3">
                    <span className="text-sm font-semibold text-text shrink-0">Test label</span>
                    <input
                      type="text"
                      value={mmTest}
                      onChange={(e) => {
                        setMmTest(e.target.value)
                        multiMediaMutation.reset()
                      }}
                      className="w-40 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                    />
                  </div>
                </div>
              </section>

              <Button
                type="button"
                variant="secondary"
                onClick={() => {
                  setMediaSlots(EXAMPLE_MEDIA)
                  setMmReference('reference')
                  setMmTest('test')
                  setActiveMediumIdx(0)
                  multiMediaMutation.reset()
                }}
                className="w-full"
              >
                Load example
              </Button>

              <Button
                onClick={() => multiMediaMutation.mutate()}
                disabled={mediaSlots.length < 2 || multiMediaMutation.isPending}
                loading={multiMediaMutation.isPending}
                size="lg"
                className="w-full"
              >
                {multiMediaMutation.isPending ? 'Comparing...' : 'Run Multi-Media f2'}
              </Button>
            </div>
          </div>

          <div className="flex-1 min-w-0 flex flex-col gap-5">
            {multiMediaMutation.isError && (
              <ErrorBanner
                message={multiMediaMutation.error.message}
                onDismiss={() => multiMediaMutation.reset()}
              />
            )}
            {!mmResult && !multiMediaMutation.isPending && !multiMediaMutation.isError && (
              <EmptyResults
                icon={Waves}
                title="Multi-media comparison results appear here"
                description="Add at least two media, align the reference and test formulations, then run the comparison."
              />
            )}

            {mmResult && !multiMediaMutation.isPending && (
              <>
                <div className="flex items-center gap-4 flex-wrap">
                  <Badge variant={mmResult.overall_pass ? 'success' : 'danger'}>
                    {mmResult.overall_pass ? 'Overall PASS (all f2 >= 50)' : 'Overall FAIL'}
                  </Badge>
                </div>

                <div className="flex gap-3 flex-wrap">
                  {mmResult.per_media.map((m) => (
                    <MetricCard
                      key={m.medium}
                      label={`f2 ${m.medium}`}
                      value={m.f2_value}
                      highlight={m.similar}
                    />
                  ))}
                </div>

                <div className="rounded-sm border border-border overflow-hidden">
                  <table className="w-full border-collapse text-sm">
                    <thead>
                      <tr>
                        <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border font-semibold text-xs">
                          Medium
                        </th>
                        <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border font-semibold text-xs">
                          f1
                        </th>
                        <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border font-semibold text-xs">
                          f2
                        </th>
                        <th className="px-3 py-2 bg-surface text-text-muted text-left border-b border-border font-semibold text-xs">
                          Status
                        </th>
                      </tr>
                    </thead>
                    <tbody>
                      {mmResult.per_media.map((m, i) => (
                        <tr key={m.medium} className={i % 2 === 0 ? 'bg-transparent' : 'bg-surface'}>
                          <td className="px-3 py-2 text-text border-b border-border">{m.medium}</td>
                          <td className="px-3 py-2 text-text border-b border-border tabular-nums">
                            {m.f1_value.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 text-text border-b border-border tabular-nums">
                            {m.f2_value.toFixed(2)}
                          </td>
                          <td className="px-3 py-2 border-b border-border">
                            <Badge variant={m.similar ? 'success' : 'danger'}>
                              {m.similar ? 'PASS' : 'FAIL'}
                            </Badge>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                {mmResult.per_media[0] && (
                  <div className="bg-surface border border-border rounded-sm p-4 lg:p-5">
                    <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
                      Profiles ({mmResult.per_media[0].medium})
                    </h3>
                    <PKChart
                      series={[
                        {
                          name: mmResult.reference_label,
                          times: mmResult.per_media[0].time_points,
                          concs: mmResult.per_media[0].reference_mean,
                          color: '#5e6ad2',
                        },
                        {
                          name: mmResult.test_label,
                          times: mmResult.per_media[0].time_points,
                          concs: mmResult.per_media[0].test_mean,
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
                )}

                <DownloadReportButton
                  formats={['html', 'pdf', 'docx']}
                  onDownload={(fmt) => downloadMultiMediaReport(mmReq, fmt)}
                />
                <Disclaimer text={mmResult.disclaimer} />
              </>
            )}
          </div>
        </AnalysisShell>
      ) : pageTab === 'workbench' ? (
        <DissolutionWorkbench />
      ) : (
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
                  onChange={(mapping) => {
                    setColumnMapping(mapping)
                    compareMutation.reset()
                  }}
                />
              </section>
            )}

            {selectableFormulations.length > 0 && (
              <section>
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                  {inputMode === 'upload' && headers.length > 0 ? '3.' : '2.'} Select Formulations
                </h3>
                <div className="space-y-2.5">
                  <div className="flex justify-between items-center gap-3">
                    <span className="text-sm font-semibold text-text shrink-0">Reference</span>
                    <UiSelect
                      value={selectedReference}
                      onChange={(e) => {
                        setReference(e.target.value)
                        compareMutation.reset()
                      }}
                      className="min-w-[150px]"
                    >
                      {selectableFormulations.map((f) => (
                        <option key={f} value={f}>{f}</option>
                      ))}
                    </UiSelect>
                  </div>
                  <div className="flex justify-between items-center gap-3">
                    <span className="text-sm font-semibold text-text shrink-0">Test</span>
                    <UiSelect
                      value={selectedTest}
                      onChange={(e) => {
                        setTest(e.target.value)
                        compareMutation.reset()
                      }}
                      className="min-w-[150px]"
                    >
                      {selectableFormulations.map((f) => (
                        <option key={f} value={f}>{f}</option>
                      ))}
                    </UiSelect>
                  </div>
                </div>
              </section>
            )}

            <Button
              onClick={runCompare}
              disabled={
                !activeFile ||
                (inputMode === 'upload' && headers.length === 0) ||
                !selectedReference ||
                !selectedTest ||
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
          {!result && !compareMutation.isPending && !compareMutation.isError && (
            <EmptyResults
              icon={Waves}
              title="Dissolution comparison results appear here"
              description="Provide matched vessel-level profiles, choose reference and test formulations, then compare."
            />
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
                formats={['html', 'markdown', 'pdf', 'docx']}
                onDownload={(fmt) =>
                  downloadDissolutionReport(activeFile!, selectedReference, selectedTest, columns, fmt)
                }
              />
              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </div>
      </AnalysisShell>
      )}
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
