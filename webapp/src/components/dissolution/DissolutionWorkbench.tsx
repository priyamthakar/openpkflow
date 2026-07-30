import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import Papa from 'papaparse'
import { Archive, FlaskConical } from 'lucide-react'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { EmptyResults } from '@/components/shared/EmptyResults'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { MetricCard } from '@/components/shared/MetricCard'
import { PasteDataGrid, type PasteDataColumn, type PasteDataRow } from '@/components/shared/PasteDataGrid'
import { PKChart } from '@/components/shared/PKChart'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import {
  analyzeDissolutionWorkbench,
  downloadDissolutionWorkbenchAudit,
  downloadDissolutionWorkbenchReport,
} from '@/lib/api'
import type {
  DissolutionRowPayload,
  WorkbenchModel,
  WorkbenchRequest,
  WorkbenchResponse,
} from '@/lib/types'
import { useRunShortcut } from '@/lib/useRunShortcut'

const COLUMNS: PasteDataColumn[] = [
  { key: 'formulation', label: 'Formulation' },
  { key: 'batch', label: 'Vessel' },
  { key: 'time', label: 'Time', type: 'number' },
  { key: 'percent_released', label: '% Released', type: 'number' },
]

const MODEL_LABELS: { value: WorkbenchModel; label: string }[] = [
  { value: 'zero_order', label: 'Zero-order' },
  { value: 'first_order', label: 'First-order' },
  { value: 'higuchi', label: 'Higuchi' },
  { value: 'korsmeyer_peppas', label: 'Korsmeyer-Peppas' },
  { value: 'weibull', label: 'Weibull' },
]

function exampleRows(): PasteDataRow[] {
  const rows: PasteDataRow[] = []
  const times = [5, 10, 15, 20, 30, 45, 60]
  const reference = [8, 19, 34, 50, 70, 88, 96]
  const test = [7, 18, 33, 49, 69, 87, 95]
  for (const [formulation, values, prefix] of [
    ['Reference', reference, 'R'],
    ['Test', test, 'T'],
  ] as const) {
    for (const [vesselIndex, offset] of [-1, 0, 1].entries()) {
      for (let index = 0; index < times.length; index += 1) {
        rows.push({
          formulation,
          batch: `${prefix}${vesselIndex + 1}`,
          time: times[index],
          percent_released: values[index] + offset,
        })
      }
    }
  }
  return rows
}

function payloadRows(rows: PasteDataRow[]): DissolutionRowPayload[] {
  return rows
    .filter(
      (row) =>
        String(row.formulation ?? '').trim() !== '' &&
        String(row.batch ?? '').trim() !== '' &&
        String(row.time ?? '').trim() !== '' &&
        String(row.percent_released ?? '').trim() !== '',
    )
    .map((row) => ({
      formulation: String(row.formulation).trim(),
      batch: String(row.batch).trim(),
      time: Number(row.time),
      percent_released: Number(row.percent_released),
    }))
}

function downloadTemplate() {
  const lines = [
    'formulation,batch,time,percent_released',
    ...payloadRows(exampleRows()).map(
      (row) => `${row.formulation},${row.batch},${row.time},${row.percent_released}`,
    ),
  ]
  const url = URL.createObjectURL(new Blob([lines.join('\n')], { type: 'text/csv' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = 'dissolution_workbench_template.csv'
  anchor.click()
  URL.revokeObjectURL(url)
}

function modelParameters(params: Record<string, number>) {
  return Object.entries(params)
    .map(([name, value]) => `${name}=${value.toPrecision(4)}`)
    .join(', ')
}

export function DissolutionWorkbench() {
  const [rows, setRows] = useState<PasteDataRow[]>(exampleRows)
  const [reference, setReference] = useState('Reference')
  const [test, setTest] = useState('Test')
  const [f2Method, setF2Method] = useState<'regulatory' | 'all_points'>('regulatory')
  const [replicates, setReplicates] = useState(1000)
  const [confidence, setConfidence] = useState(0.9)
  const [seed, setSeed] = useState(2026)
  const [comparisonModel, setComparisonModel] = useState<WorkbenchModel>('weibull')
  const [inputError, setInputError] = useState('')
  const [auditPending, setAuditPending] = useState(false)
  const [auditError, setAuditError] = useState('')

  const formulations = useMemo(
    () =>
      Array.from(
        new Set(rows.map((row) => String(row.formulation ?? '').trim()).filter(Boolean)),
      ),
    [rows],
  )
  const request = useMemo<WorkbenchRequest>(
    () => ({
      rows: payloadRows(rows),
      config: {
        reference_label: reference,
        test_label: test,
        f2_method: f2Method,
        bootstrap_replicates: replicates,
        confidence_level: confidence,
        seed,
        model_comparison_model: comparisonModel,
        model_comparison_param_index: 0,
      },
    }),
    [rows, reference, test, f2Method, replicates, confidence, seed, comparisonModel],
  )

  const mutation = useMutation<WorkbenchResponse, Error>({
    mutationFn: () => analyzeDissolutionWorkbench(request),
  })
  const result = mutation.data
  const canRun =
    request.rows.length > 0 &&
    reference.length > 0 &&
    test.length > 0 &&
    reference !== test &&
    !mutation.isPending
  useRunShortcut(mutation.mutate, canRun)

  function resetResult() {
    mutation.reset()
    setAuditError('')
  }

  function loadCsv(file: File) {
    setInputError('')
    Papa.parse<Record<string, string>>(file, {
      header: true,
      skipEmptyLines: true,
      complete: (parsed) => {
        const required = COLUMNS.map((column) => column.key)
        const headers = parsed.meta.fields ?? []
        const missing = required.filter((column) => !headers.includes(column))
        if (missing.length > 0) {
          setInputError(`CSV is missing required columns: ${missing.join(', ')}`)
          return
        }
        const parsedRows = parsed.data.map((row) => ({
          formulation: row.formulation,
          batch: row.batch,
          time: row.time,
          percent_released: row.percent_released,
        }))
        setRows(parsedRows)
        const labels = Array.from(
          new Set(parsedRows.map((row) => String(row.formulation).trim()).filter(Boolean)),
        )
        setReference(labels[0] ?? '')
        setTest(labels[1] ?? '')
        resetResult()
      },
      error: (error) => setInputError(error.message),
    })
  }

  const chartSeries = result
    ? [
        ...result.vessel_profiles.reference.map((profile) => ({
          name: `${profile.formulation} ${profile.vessel_id}`,
          times: profile.time_points,
          concs: profile.percent_released,
          color: '#93b7d6',
        })),
        ...result.vessel_profiles.test.map((profile) => ({
          name: `${profile.formulation} ${profile.vessel_id}`,
          times: profile.time_points,
          concs: profile.percent_released,
          color: '#efb092',
          dashed: true,
        })),
        {
          name: `${result.similarity.reference_label} mean`,
          times: result.similarity.time_points,
          concs: result.similarity.reference_mean,
          color: '#1f5c8c',
        },
        {
          name: `${result.similarity.test_label} mean`,
          times: result.similarity.time_points,
          concs: result.similarity.test_mean,
          color: '#bd4d22',
          dashed: true,
        },
      ]
    : []

  return (
    <AnalysisShell leftWide resultKey={Boolean(result)}>
      <div className="flex flex-col gap-4">
        <section>
          <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
            1. Vessel-Level Input
          </h3>
          <FileDropzone
            onFile={loadCsv}
            onClear={() => {
              setRows([])
              resetResult()
            }}
            label="Upload vessel-level CSV"
          />
          <button
            type="button"
            onClick={downloadTemplate}
            className="mt-2 text-xs text-text-muted underline underline-offset-2 hover:text-text"
          >
            Download workbench template CSV
          </button>
          <div className="mt-3">
            <PasteDataGrid
              columns={COLUMNS}
              rows={rows}
              onChange={(nextRows) => {
                setRows(nextRows)
                resetResult()
              }}
              filename="dissolution_workbench_input.csv"
              hint="Each vessel must contain the same matched time points. Uploaded rows remain editable."
            />
          </div>
          {inputError && <ErrorBanner message={inputError} className="mt-3" />}
        </section>

        <section>
          <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
            2. Analysis Configuration
          </h3>
          <div className="space-y-2.5">
            <label className="flex items-center justify-between gap-3 text-sm font-semibold">
              Reference
              <Select
                aria-label="Workbench reference"
                value={reference}
                onChange={(event) => {
                  setReference(event.target.value)
                  resetResult()
                }}
                className="min-w-[160px] bg-surface-2 text-text"
              >
                {formulations.map((label) => (
                  <option key={label} value={label}>{label}</option>
                ))}
              </Select>
            </label>
            <label className="flex items-center justify-between gap-3 text-sm font-semibold">
              Test
              <Select
                aria-label="Workbench test"
                value={test}
                onChange={(event) => {
                  setTest(event.target.value)
                  resetResult()
                }}
                className="min-w-[160px] bg-surface-2 text-text"
              >
                {formulations.map((label) => (
                  <option key={label} value={label}>{label}</option>
                ))}
              </Select>
            </label>
            <label className="flex items-center justify-between gap-3 text-sm font-semibold">
              Point f2 method
              <Select
                aria-label="Point f2 method"
                value={f2Method}
                onChange={(event) => {
                  setF2Method(event.target.value as 'regulatory' | 'all_points')
                  resetResult()
                }}
                className="min-w-[160px] bg-surface-2 text-text"
              >
                <option value="regulatory">Regulatory 85% rule</option>
                <option value="all_points">All points</option>
              </Select>
            </label>
            <label className="flex items-center justify-between gap-3 text-sm font-semibold">
              Bootstrap replicates
              <Input
                aria-label="Bootstrap replicates"
                type="number"
                min={100}
                max={100000}
                value={replicates}
                onChange={(event) => {
                  setReplicates(Number(event.target.value))
                  resetResult()
                }}
                className="w-40"
              />
            </label>
            <label className="flex items-center justify-between gap-3 text-sm font-semibold">
              Confidence level
              <Select
                aria-label="Bootstrap confidence level"
                value={confidence}
                onChange={(event) => {
                  setConfidence(Number(event.target.value))
                  resetResult()
                }}
                className="w-40 bg-surface-2 text-text"
              >
                <option value={0.9}>90%</option>
                <option value={0.95}>95%</option>
              </Select>
            </label>
            <label className="flex items-center justify-between gap-3 text-sm font-semibold">
              Random seed
              <Input
                aria-label="Bootstrap random seed"
                type="number"
                value={seed}
                onChange={(event) => {
                  setSeed(Number(event.target.value))
                  resetResult()
                }}
                className="w-40"
              />
            </label>
            <label className="flex items-center justify-between gap-3 text-sm font-semibold">
              Parameter comparison
              <Select
                aria-label="Model parameter comparison"
                value={comparisonModel}
                onChange={(event) => {
                  setComparisonModel(event.target.value as WorkbenchModel)
                  resetResult()
                }}
                className="min-w-[160px] bg-surface-2 text-text"
              >
                {MODEL_LABELS.map((model) => (
                  <option key={model.value} value={model.value}>{model.label}</option>
                ))}
              </Select>
            </label>
          </div>
        </section>

        <Button
          variant="secondary"
          onClick={() => {
            setRows(exampleRows())
            setReference('Reference')
            setTest('Test')
            resetResult()
          }}
          className="w-full"
        >
          Load example
        </Button>
        <Button
          onClick={() => mutation.mutate()}
          disabled={!canRun}
          loading={mutation.isPending}
          size="lg"
          className="w-full"
        >
          {mutation.isPending ? 'Running workbench...' : 'Run Advanced Workbench'}
        </Button>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-5">
        {mutation.isError && (
          <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />
        )}
        {!result && !mutation.isPending && !mutation.isError && (
          <EmptyResults
            icon={FlaskConical}
            title="Advanced workbench results appear here"
            description="Provide matched vessel profiles to run point and bootstrap f2, five validated models, alternative metrics, reports, and an audit bundle."
          />
        )}
        {result && !mutation.isPending && (
          <>
            <div className="flex flex-wrap items-center gap-3">
              <Badge variant={result.similarity.similar ? 'success' : 'danger'}>
                Point f2 {result.similarity.similar ? 'supports similarity' : 'does not support similarity'}
              </Badge>
              <Badge variant={result.bootstrap_f2.is_similar ? 'success' : 'danger'}>
                Bootstrap CI {result.bootstrap_f2.is_similar ? 'supports similarity' : 'does not support similarity'}
              </Badge>
            </div>

            <div className="flex flex-wrap gap-3">
              <MetricCard label="f1" value={result.similarity.f1_value} />
              <MetricCard label="f2" value={result.similarity.f2_value} highlight={result.similarity.similar} />
              <MetricCard label="Bootstrap CI lower" value={result.bootstrap_f2.ci_lower} />
              <MetricCard label="Bootstrap CI upper" value={result.bootstrap_f2.ci_upper} />
              <MetricCard label="Max deviation" value={result.alternatives.maximum_deviation} />
              <MetricCard label="MSD squared" value={result.alternatives.msd_squared} />
            </div>

            <div className="rounded-sm border border-border bg-surface p-4 lg:p-5">
              <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-muted">
                Mean and Vessel Profiles
              </h3>
              <PKChart
                series={chartSeries}
                xLabel="Time (min)"
                yLabel="% Dissolved"
                thresholdY={85}
                thresholdLabel="85% threshold"
              />
            </div>

            <div className="overflow-hidden rounded-sm border border-border">
              <div className="border-b border-border bg-surface px-3 py-2">
                <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Five-Model AICc Ranking
                </h3>
              </div>
              <div className="overflow-x-auto">
                <table className="w-full border-collapse text-sm">
                  <thead>
                    <tr>
                      {['Formulation', 'Rank', 'Model', 'Parameters', 'R2', 'AICc'].map((label) => (
                        <th key={label} className="border-b border-border bg-surface px-3 py-2 text-left text-xs font-semibold text-text-muted">
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {(['reference', 'test'] as const).flatMap((side) =>
                      result.model_fits[side].fits
                        .filter((fit) => fit.converged)
                        .map((fit, rank) => (
                          <tr key={`${side}-${fit.model_name}`}>
                            <td className="border-b border-border px-3 py-2 text-text">
                              {result.model_fits[side].formulation_label}
                            </td>
                            <td className="border-b border-border px-3 py-2 text-text">{rank + 1}</td>
                            <td className="border-b border-border px-3 py-2 font-semibold text-text">
                              {fit.model_name}
                            </td>
                            <td className="border-b border-border px-3 py-2 text-text-muted">
                              {modelParameters(fit.params)}
                            </td>
                            <td className="border-b border-border px-3 py-2 tabular-nums text-text">
                              {fit.r_squared?.toFixed(4) ?? '-'}
                            </td>
                            <td className="border-b border-border px-3 py-2 tabular-nums text-text">
                              {fit.aicc?.toFixed(2) ?? '-'}
                            </td>
                          </tr>
                        )),
                    )}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="rounded-sm border border-border bg-surface p-4 text-sm text-text">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
                Model-Dependent Comparison
              </h3>
              <p>
                {result.model_comparison.model_name} / {result.model_comparison.param_name}:
                {' '}{result.model_comparison.ratio_pct.toFixed(2)}% ratio,
                90% CI {result.model_comparison.ci_lo.toFixed(2)}-
                {result.model_comparison.ci_hi.toFixed(2)}%.
              </p>
              <div className="mt-2">
                <Badge variant={result.model_comparison.is_similar ? 'success' : 'danger'}>
                  {result.model_comparison.is_similar ? 'Within 80-125%' : 'Outside 80-125%'}
                </Badge>
              </div>
            </div>

            {result.warnings.length > 0 && (
              <div className="rounded-sm border border-warning/20 bg-warning/5 p-3 text-sm text-warning">
                <p className="mb-1 font-semibold">Warnings and prerequisites</p>
                {result.warnings.map((warning, index) => (
                  <p key={index}>&bull; {warning}</p>
                ))}
              </div>
            )}

            <div className="flex flex-col gap-3 sm:flex-row sm:items-start">
              <DownloadReportButton
                formats={['html', 'pdf', 'docx']}
                onDownload={(format) => downloadDissolutionWorkbenchReport(request, format)}
              />
              <Button
                variant="secondary"
                disabled={auditPending}
                loading={auditPending}
                onClick={async () => {
                  setAuditPending(true)
                  setAuditError('')
                  try {
                    await downloadDissolutionWorkbenchAudit(request)
                  } catch (error) {
                    setAuditError((error as Error).message)
                  } finally {
                    setAuditPending(false)
                  }
                }}
              >
                <Archive size={15} />
                {auditPending ? 'Building audit bundle...' : 'Download Audit ZIP'}
              </Button>
            </div>
            {auditError && <ErrorBanner message={auditError} />}
            <p className="text-xs text-text-muted">
              The audit ZIP contains normalized input, exact configuration, serialized results,
              the HTML report, and SHA-256 checksums.
            </p>
            <Disclaimer text={result.disclaimer} />
          </>
        )}
      </div>
    </AnalysisShell>
  )
}
