import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { FlaskConical, RotateCcw } from 'lucide-react'
import { TopBar } from '@/components/layout/TopBar'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { MetricCard } from '@/components/shared/MetricCard'
import { PasteDataGrid, type PasteDataColumn, type PasteDataRow } from '@/components/shared/PasteDataGrid'
import { PKChart } from '@/components/shared/PKChart'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { analyzeSparseNca, downloadSparseNcaReport } from '@/lib/api'
import { useRunShortcut } from '@/lib/useRunShortcut'
import type { SparseNcaRequest, SparseNcaResponse } from '@/lib/types'

const COLUMNS: PasteDataColumn[] = [
  { key: 'time', label: 'Time (h)', type: 'number' },
  { key: 'concentration', label: 'Concentration', type: 'number' },
]

const THEOPH_EXAMPLE: PasteDataRow[] = [
  { time: 0.25, concentration: 2.84 },
  { time: 1.12, concentration: 10.5 },
  { time: 3.82, concentration: 8.58 },
  { time: 9.05, concentration: 6.89 },
  { time: 24.37, concentration: 3.28 },
]

export default function SparseNcaPage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [subject, setSubject] = useState('Theoph subject 1')
  const [dose, setDose] = useState(320)
  const [rows, setRows] = useState<PasteDataRow[]>(THEOPH_EXAMPLE)

  const samples = useMemo(
    () =>
      rows
        .filter(
          (row) =>
            String(row.time ?? '').trim() !== '' &&
            String(row.concentration ?? '').trim() !== '',
        )
        .map((row) => ({ time: Number(row.time), concentration: Number(row.concentration) })),
    [rows],
  )

  const request = useMemo<SparseNcaRequest>(
    () => ({
      subject,
      dose,
      times: samples.map((sample) => sample.time),
      concentrations: samples.map((sample) => sample.concentration),
    }),
    [subject, dose, samples],
  )

  const mutation = useMutation<SparseNcaResponse, Error>({
    mutationFn: () => analyzeSparseNca(request),
  })
  const result = mutation.data
  const finiteSamples = samples.every(
    (sample) => Number.isFinite(sample.time) && Number.isFinite(sample.concentration),
  )
  const canRun = samples.length >= 3 && finiteSamples && dose > 0 && !mutation.isPending

  useRunShortcut(mutation.mutate, canRun)

  function resetExample() {
    setSubject('Theoph subject 1')
    setDose(320)
    setRows(THEOPH_EXAMPLE)
    mutation.reset()
  }

  return (
    <div className="flex h-full flex-col">
      <TopBar
        title="Sparse NCA"
        subtitle="Model-informed one-compartment oral screening from 3-5 samples"
        onMenuClick={onMenuClick}
      />

      <AnalysisShell leftWide resultKey={Boolean(result)}>
        <div className="flex flex-col gap-5">
          <section className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
            <p className="font-semibold">Screening scope</p>
            <p className="mt-1">
              Fits a three-parameter oral model. Use only when the one-compartment assumptions are defensible and validate against rich sampling before decision use.
            </p>
          </section>

          <section>
            <div className="mb-2.5 flex items-center justify-between gap-3">
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
                1. Study details
              </h3>
              <Button variant="ghost" size="sm" onClick={resetExample}>
                <RotateCcw size={13} /> Load Theoph example
              </Button>
            </div>
            <div className="space-y-2.5">
              <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">
                Subject
                <input
                  aria-label="Subject"
                  value={subject}
                  onChange={(event) => {
                    setSubject(event.target.value)
                    mutation.reset()
                  }}
                  className="w-52 rounded-sm border border-border-2 bg-surface-2 px-2.5 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
                />
              </label>
              <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">
                Oral dose (mg)
                <input
                  aria-label="Oral dose"
                  type="number"
                  min="0.001"
                  step="0.1"
                  value={dose}
                  onChange={(event) => {
                    setDose(Number(event.target.value))
                    mutation.reset()
                  }}
                  className="w-28 rounded-sm border border-border-2 bg-surface-2 px-2.5 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
                />
              </label>
            </div>
          </section>

          <section>
            <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
              2. Sparse samples
            </h3>
            <PasteDataGrid
              columns={COLUMNS}
              rows={rows}
              onChange={(nextRows) => {
                setRows(nextRows)
                mutation.reset()
              }}
              filename="sparse_nca_samples.csv"
              hint="Enter 3-5 chronological samples. Times must be unique and strictly increasing."
            />
          </section>

          <Button
            size="lg"
            className="w-full"
            onClick={() => mutation.mutate()}
            disabled={!canRun}
            loading={mutation.isPending}
          >
            {mutation.isPending ? 'Fitting model...' : 'Run Sparse NCA'}
          </Button>
          {samples.length < 3 && (
            <p className="text-center text-xs text-danger">At least three complete samples are required.</p>
          )}
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {mutation.isError && (
            <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />
          )}
          {mutation.isPending && <LoadingState />}
          {!result && !mutation.isPending && !mutation.isError && <EmptyState />}

          {result && !mutation.isPending && (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-text">{result.subject || 'Sparse NCA result'}</h2>
                  <p className="text-sm text-text-muted">One-compartment oral model - {result.n_samples} samples</p>
                </div>
                <Badge variant={result.converged ? 'success' : 'danger'}>
                  {result.converged ? 'Fit converged' : 'Fit not converged'}
                </Badge>
              </div>

              {result.warnings.length > 0 && (
                <div className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
                  <p className="mb-1 font-semibold">Fit diagnostics</p>
                  {result.warnings.map((warning) => <p key={warning}>&bull; {warning}</p>)}
                </div>
              )}

              <div className="flex flex-wrap gap-3">
                <MetricCard label="CL/F" value={result.CL_F} unit="L/h" highlight />
                <MetricCard label="Vz/F" value={result.Vz_F} unit="L" />
                <MetricCard label="ka" value={result.ka} unit="1/h" />
                <MetricCard label="Half-life" value={result.half_life} unit="h" />
                <MetricCard label="AUCinf" value={result.AUCinf} />
                <MetricCard label="Cmax" value={result.Cmax} />
                <MetricCard label="Tmax" value={result.Tmax} unit="h" />
              </div>

              <section className="rounded-sm border border-border bg-surface p-4 lg:p-5">
                <h3 className="mb-3 text-xs font-semibold uppercase tracking-wider text-text-muted">
                  Observed and fitted concentrations
                </h3>
                <PKChart
                  series={[
                    { name: 'Observed', times: result.time_points, concs: result.observed_conc, color: '#e5534b' },
                    { name: 'Fitted', times: result.time_points, concs: result.fitted_conc, color: '#3dd68c', dashed: true },
                  ]}
                />
              </section>

              <ObservedFittedTable result={result} />
              <p className="rounded-sm border border-warning/20 bg-warning/5 p-3 text-sm text-warning">
                {result.scope_note}
              </p>
              <DownloadReportButton
                formats={['html', 'markdown']}
                onDownload={(format) => downloadSparseNcaReport(request, format)}
              />
              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </div>
      </AnalysisShell>
    </div>
  )
}

function LoadingState() {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-3">
        {[1, 2, 3, 4].map((item) => <Skeleton key={item} className="h-24 w-36 rounded-sm" />)}
      </div>
      <Skeleton className="h-80 w-full rounded-sm" />
    </div>
  )
}

function EmptyState() {
  return (
    <div className="flex min-h-72 flex-col items-center justify-center rounded-sm border border-dashed border-border-2 bg-surface/40 p-8 text-center">
      <FlaskConical size={32} className="mb-3 text-text-dim" />
      <h2 className="font-semibold text-text">Sparse fit results appear here</h2>
      <p className="mt-1 max-w-md text-sm text-text-muted">
        Review the example or enter chronological oral PK samples, then run the model-informed fit.
      </p>
    </div>
  )
}

function ObservedFittedTable({ result }: { result: SparseNcaResponse }) {
  return (
    <div className="overflow-x-auto rounded-sm border border-border">
      <table className="w-full border-collapse text-sm">
        <thead><tr><th className="bg-surface-2 px-3 py-2 text-left text-xs text-text-muted">Time</th><th className="bg-surface-2 px-3 py-2 text-left text-xs text-text-muted">Observed</th><th className="bg-surface-2 px-3 py-2 text-left text-xs text-text-muted">Fitted</th></tr></thead>
        <tbody>{result.time_points.map((time, index) => <tr key={`${time}-${index}`}><td className="border-t border-border px-3 py-2 text-text">{time.toFixed(3)}</td><td className="border-t border-border px-3 py-2 text-text">{result.observed_conc[index].toFixed(3)}</td><td className="border-t border-border px-3 py-2 text-text">{result.fitted_conc[index].toFixed(3)}</td></tr>)}</tbody>
      </table>
    </div>
  )
}
