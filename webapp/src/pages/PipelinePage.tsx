import { useCallback, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { Archive, CheckCircle2, Circle, FileCheck2 } from 'lucide-react'
import { TopBar } from '@/components/layout/TopBar'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { FileDropzone } from '@/components/shared/FileDropzone'
import { MetricCard } from '@/components/shared/MetricCard'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Select } from '@/components/ui/Select'
import { Skeleton } from '@/components/ui/Skeleton'
import {
  analyzePipeline,
  downloadPipelineAuditBundle,
  downloadPipelineReport,
} from '@/lib/api'
import { useRunShortcut } from '@/lib/useRunShortcut'
import type { PipelineFiles, PipelineOptions, PipelineResponse } from '@/lib/types'

const DEFAULT_OPTIONS: PipelineOptions = {
  title: 'OpenPKFlow Study Report',
  dissolution_reference: 'reference',
  dissolution_test: 'test',
  nca_auc_method: 'linear_up_log_down',
  nca_blq_method: 'none',
  be_parameter: 'AUCinf',
  be_reference_col: 'reference',
  be_test_col: 'test',
  be_subject_col: 'subject',
  be_sequence_col: 'sequence',
  be_lower: 0.8,
  be_upper: 1.25,
}

export default function PipelinePage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [files, setFiles] = useState<PipelineFiles>({})
  const [options, setOptions] = useState<PipelineOptions>(DEFAULT_OPTIONS)
  const [auditPending, setAuditPending] = useState(false)
  const [downloadError, setDownloadError] = useState('')

  const mutation = useMutation<PipelineResponse, Error>({
    mutationFn: () => analyzePipeline(files, options),
  })

  const updateFile = useCallback(
    (stage: keyof PipelineFiles, file: File | null) => {
      setFiles((current) => ({ ...current, [stage]: file }))
      mutation.reset()
      setDownloadError('')
    },
    [mutation],
  )

  const updateOption = useCallback(
    <K extends keyof PipelineOptions>(key: K, value: PipelineOptions[K]) => {
      setOptions((current) => ({ ...current, [key]: value }))
      mutation.reset()
      setDownloadError('')
    },
    [mutation],
  )

  const selectedStages = useMemo(
    () => (['dissolution', 'nca', 'be'] as const).filter((stage) => Boolean(files[stage])),
    [files],
  )
  const canRun = selectedStages.length > 0 && !mutation.isPending
  const result = mutation.data

  useRunShortcut(mutation.mutate, canRun)

  async function downloadAuditBundle() {
    setAuditPending(true)
    setDownloadError('')
    try {
      await downloadPipelineAuditBundle(files, options)
    } catch (error) {
      setDownloadError((error as Error).message)
    } finally {
      setAuditPending(false)
    }
  }

  return (
    <div className="flex h-full flex-col">
      <TopBar
        title="Study Pipeline"
        subtitle="Run dissolution, NCA, and paired BE stages with one audit-ready output"
        onMenuClick={onMenuClick}
      />

      <AnalysisShell leftWide resultKey={Boolean(result)}>
        <div className="flex flex-col gap-5">
          <section>
            <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
              1. Study identity
            </h3>
            <label className="block text-sm font-semibold text-text" htmlFor="pipeline-title">
              Report title
            </label>
            <input
              id="pipeline-title"
              value={options.title}
              onChange={(event) => updateOption('title', event.target.value)}
              className="mt-1.5 w-full rounded-sm border border-border-2 bg-surface-2 px-3 py-2 text-sm font-semibold text-text focus:border-accent focus:outline-none focus:ring-2 focus:ring-accent/30"
            />
          </section>

          <section>
            <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
              2. Stage inputs
            </h3>
            <p className="mb-3 text-sm text-text-muted">
              Upload one or more stages. Each CSV is processed by the validated core library.
            </p>
            <div className="grid gap-3 sm:grid-cols-3 md:grid-cols-1 xl:grid-cols-3">
              <StageUpload
                label="Dissolution CSV"
                selected={Boolean(files.dissolution)}
                onFile={(file) => updateFile('dissolution', file)}
                onClear={() => updateFile('dissolution', null)}
              />
              <StageUpload
                label="NCA CSV"
                selected={Boolean(files.nca)}
                onFile={(file) => updateFile('nca', file)}
                onClear={() => updateFile('nca', null)}
              />
              <StageUpload
                label="BE CSV"
                selected={Boolean(files.be)}
                onFile={(file) => updateFile('be', file)}
                onClear={() => updateFile('be', null)}
              />
            </div>
          </section>

          {files.dissolution && (
            <StageOptions title="Dissolution options">
              <TextOption
                label="Reference label"
                value={options.dissolution_reference ?? ''}
                onChange={(value) => updateOption('dissolution_reference', value)}
              />
              <TextOption
                label="Test label"
                value={options.dissolution_test ?? ''}
                onChange={(value) => updateOption('dissolution_test', value)}
              />
            </StageOptions>
          )}

          {files.nca && (
            <StageOptions title="NCA options">
              <SelectOption label="AUC method">
                <Select
                  value={options.nca_auc_method ?? ''}
                  onChange={(event) =>
                    updateOption(
                      'nca_auc_method',
                      event.target.value as PipelineOptions['nca_auc_method'],
                    )
                  }
                >
                  <option value="linear">Linear</option>
                  <option value="log">Log</option>
                  <option value="linear_up_log_down">Linear-up/log-down</option>
                </Select>
              </SelectOption>
              <SelectOption label="BLQ method">
                <Select
                  value={options.nca_blq_method ?? ''}
                  onChange={(event) =>
                    updateOption(
                      'nca_blq_method',
                      event.target.value as PipelineOptions['nca_blq_method'],
                    )
                  }
                >
                  {['none', 'drop', 'zero', 'half_lloq', 'lloq', 'm1', 'm2'].map((method) => (
                    <option key={method} value={method}>{method}</option>
                  ))}
                </Select>
              </SelectOption>
            </StageOptions>
          )}

          {files.be && (
            <StageOptions title="BE options">
              <TextOption
                label="Parameter"
                value={options.be_parameter}
                onChange={(value) => updateOption('be_parameter', value)}
              />
              <NumberOption
                label="Lower limit"
                value={options.be_lower}
                onChange={(value) => updateOption('be_lower', value)}
              />
              <NumberOption
                label="Upper limit"
                value={options.be_upper}
                onChange={(value) => updateOption('be_upper', value)}
              />
            </StageOptions>
          )}

          <Button
            onClick={() => mutation.mutate()}
            disabled={!canRun}
            loading={mutation.isPending}
            size="lg"
            className="w-full"
          >
            {mutation.isPending ? 'Running pipeline...' : 'Run Study Pipeline'}
          </Button>
          {!selectedStages.length && (
            <p className="text-center text-xs text-text-muted">Upload at least one stage CSV.</p>
          )}
        </div>

        <div className="flex min-w-0 flex-1 flex-col gap-5">
          {mutation.isError && (
            <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />
          )}
          {downloadError && (
            <ErrorBanner message={downloadError} onDismiss={() => setDownloadError('')} />
          )}

          {mutation.isPending && (
            <div className="space-y-5">
              <div className="flex flex-wrap gap-3">
                <Skeleton className="h-24 w-40 rounded-sm" />
                <Skeleton className="h-24 w-40 rounded-sm" />
                <Skeleton className="h-24 w-40 rounded-sm" />
              </div>
              <Skeleton className="h-64 w-full rounded-sm" />
            </div>
          )}

          {!result && !mutation.isPending && !mutation.isError && <EmptyState />}

          {result && !mutation.isPending && (
            <>
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-bold text-text">{result.metadata.title}</h2>
                  <p className="text-sm text-text-muted">
                    OpenPKFlow {result.metadata.openpkflow_version} - {result.metadata.stages_completed.length} stage(s) completed
                  </p>
                </div>
                <Badge variant="success">Pipeline complete</Badge>
              </div>

              <StageStatus metadata={result.metadata} />

              {result.metadata.warnings.length > 0 && (
                <div className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
                  <p className="mb-1 font-semibold">Pipeline warnings</p>
                  {result.metadata.warnings.map((warning) => <p key={warning}>&bull; {warning}</p>)}
                </div>
              )}

              {result.dissolution && (
                <ResultSection title="Dissolution similarity">
                  <div className="flex flex-wrap gap-3">
                    <MetricCard label="f1" value={result.dissolution.f1_value} />
                    <MetricCard label="f2" value={result.dissolution.f2_value} highlight />
                    <MetricCard label="Time points" value={result.dissolution.n_timepoints} />
                  </div>
                  <p className="text-sm text-text-muted">
                    {result.dissolution.reference_label} vs {result.dissolution.test_label} - {result.dissolution.f2_value >= 50 ? 'similar' : 'not similar'} by the f2 &gt;= 50 threshold.
                  </p>
                </ResultSection>
              )}

              {result.nca && (
                <ResultSection title="Non-compartmental analysis">
                  <div className="flex flex-wrap gap-3">
                    <MetricCard label="Subjects" value={result.nca.n_subjects} highlight />
                    <MetricCard label="AUC method" value={result.nca.auc_method} />
                    <MetricCard label="BLQ method" value={result.nca.blq_method} />
                  </div>
                  <NcaTable rows={result.nca.subjects} />
                </ResultSection>
              )}

              {result.be && (
                <ResultSection title="Paired bioequivalence">
                  <div className="flex flex-wrap gap-3">
                    <MetricCard label="GMR" value={result.be.gmr} highlight />
                    <MetricCard label="90% CI lower" value={result.be.gmr_lower_90ci} />
                    <MetricCard label="90% CI upper" value={result.be.gmr_upper_90ci} />
                    <MetricCard label="CV intra" value={result.be.cv_intra_pct} unit="%" />
                  </div>
                  <Badge variant={result.be.bioequivalent ? 'success' : 'danger'}>
                    {result.be.bioequivalent ? 'BIOEQUIVALENT' : 'NOT BIOEQUIVALENT'}
                  </Badge>
                </ResultSection>
              )}

              <div className="flex flex-col items-stretch gap-3 sm:flex-row sm:items-start">
                <DownloadReportButton
                  formats={['html', 'markdown']}
                  onDownload={(format) => downloadPipelineReport(files, options, format)}
                />
                <Button
                  variant="secondary"
                  onClick={downloadAuditBundle}
                  disabled={auditPending}
                  loading={auditPending}
                  className="gap-2"
                >
                  <Archive size={15} />
                  {auditPending ? 'Building audit bundle...' : 'Download Audit ZIP'}
                </Button>
              </div>
              <p className="text-xs text-text-muted">
                The audit ZIP includes normalized inputs, configuration, serialized results, HTML report, and SHA-256 manifest.
              </p>
              <Disclaimer text={result.disclaimer} />
            </>
          )}
        </div>
      </AnalysisShell>
    </div>
  )
}

function StageUpload({
  label,
  selected,
  onFile,
  onClear,
}: {
  label: string
  selected: boolean
  onFile: (file: File) => void
  onClear: () => void
}) {
  return (
    <div className="min-w-0">
      <div className="mb-1.5 flex items-center gap-1.5 text-sm font-semibold text-text">
        {selected ? <CheckCircle2 size={14} className="text-success" /> : <Circle size={14} className="text-text-dim" />}
        {label}
      </div>
      <FileDropzone onFile={onFile} onClear={onClear} label={`Upload ${label}`} />
    </div>
  )
}

function StageOptions({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="rounded-sm border border-border bg-surface p-3">
      <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">{title}</h3>
      <div className="space-y-2.5">{children}</div>
    </section>
  )
}

function TextOption({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">
      {label}
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        className="w-36 rounded-sm border border-border-2 bg-surface-2 px-2.5 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
      />
    </label>
  )
}

function NumberOption({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">
      {label}
      <input
        type="number"
        step="0.01"
        value={value}
        onChange={(event) => onChange(Number(event.target.value))}
        className="w-24 rounded-sm border border-border-2 bg-surface-2 px-2.5 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
      />
    </label>
  )
}

function SelectOption({ label, children }: { label: string; children: React.ReactNode }) {
  return <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">{label}{children}</label>
}

function EmptyState() {
  return (
    <div className="flex min-h-72 flex-col items-center justify-center rounded-sm border border-dashed border-border-2 bg-surface/40 p-8 text-center">
      <FileCheck2 size={32} className="mb-3 text-text-dim" />
      <h2 className="font-semibold text-text">Unified study results appear here</h2>
      <p className="mt-1 max-w-md text-sm text-text-muted">
        Combine any available study stages, inspect their status, then download one report and a reproducibility bundle.
      </p>
    </div>
  )
}

function StageStatus({ metadata }: { metadata: PipelineResponse['metadata'] }) {
  return (
    <div className="grid gap-2 sm:grid-cols-3">
      {metadata.stages_requested.map((stage) => {
        const completed = metadata.stage_status[stage] === 'completed'
        return (
          <div key={stage} className="flex items-center gap-2 rounded-sm border border-border bg-surface p-3">
            {completed ? <CheckCircle2 size={16} className="text-success" /> : <Circle size={16} className="text-warning" />}
            <div>
              <p className="text-xs font-semibold uppercase tracking-wider text-text-muted">{stage}</p>
              <p className="text-sm font-semibold text-text">{metadata.stage_status[stage]}</p>
            </div>
          </div>
        )
      })}
    </div>
  )
}

function ResultSection({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-3 rounded-sm border border-border bg-surface p-4">
      <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted">{title}</h3>
      {children}
    </section>
  )
}

function NcaTable({ rows }: { rows: Record<string, number | string | null>[] }) {
  if (!rows.length) return null
  const preferred = ['subject', 'AUClast', 'AUCinf_obs', 'Cmax', 'Tmax', 'half_life', 'CL_F', 'CL']
  const columns = preferred.filter((column) => column in rows[0]).slice(0, 6)
  return (
    <div className="overflow-x-auto rounded-sm border border-border">
      <table className="w-full border-collapse text-sm">
        <thead><tr>{columns.map((column) => <th key={column} className="border-b border-border bg-surface-2 px-3 py-2 text-left text-xs font-semibold text-text-muted">{column}</th>)}</tr></thead>
        <tbody>{rows.map((row, index) => <tr key={String(row.subject ?? index)}>{columns.map((column) => <td key={column} className="border-b border-border px-3 py-2 text-text tabular-nums">{formatValue(row[column])}</td>)}</tr>)}</tbody>
      </table>
    </div>
  )
}

function formatValue(value: number | string | null) {
  if (typeof value === 'number') return Number.isFinite(value) ? value.toFixed(3) : 'Not available'
  return value ?? 'Not available'
}
