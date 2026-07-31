import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { RotateCcw, ShieldCheck } from 'lucide-react'
import { TopBar } from '@/components/layout/TopBar'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { EmptyResults } from '@/components/shared/EmptyResults'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { MetricCard } from '@/components/shared/MetricCard'
import { PasteDataGrid, type PasteDataColumn, type PasteDataRow } from '@/components/shared/PasteDataGrid'
import { Badge } from '@/components/ui/Badge'
import { Button } from '@/components/ui/Button'
import { Skeleton } from '@/components/ui/Skeleton'
import { assessAlcoholDosing, classifySupac } from '@/lib/api'
import { useRunShortcut } from '@/lib/useRunShortcut'
import type {
  AlcoholDosingRequest,
  AlcoholDosingResponse,
  SupacClassifyRequest,
  SupacClassifyResponse,
  SupacComponentCategory,
} from '@/lib/types'

type Tab = 'supac' | 'alcohol'

const COMPONENT_OPTIONS: { value: SupacComponentCategory; label: string }[] = [
  { value: 'filler', label: 'Filler' },
  { value: 'binder', label: 'Binder' },
  { value: 'disintegrant_starch', label: 'Disintegrant (starch)' },
  { value: 'disintegrant_other', label: 'Disintegrant (other)' },
  { value: 'lubricant_stearate', label: 'Lubricant (stearate)' },
  { value: 'lubricant_other', label: 'Lubricant (other)' },
  { value: 'glidant', label: 'Glidant' },
  { value: 'film_coat', label: 'Film coat' },
]

const CONTROL_EXAMPLE: PasteDataRow[] = [
  { time: 5, concentration: 45 },
  { time: 10, concentration: 70 },
  { time: 15, concentration: 85 },
  { time: 20, concentration: 92 },
  { time: 30, concentration: 96 },
]

const ETHANOL_EXAMPLE: PasteDataRow[] = [
  { ethanol_pct: 5, p0: 44, p1: 69, p2: 84, p3: 91, p4: 95 },
  { ethanol_pct: 20, p0: 60, p1: 88, p2: 95, p3: 98, p4: 99 },
  { ethanol_pct: 40, p0: 82, p1: 97, p2: 99, p3: 100, p4: 100 },
]

export default function SupacPage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [tab, setTab] = useState<Tab>('supac')

  return (
    <div className="flex h-full flex-col">
      <TopBar
        title="SUPAC & Alcohol Screening"
        subtitle="SUPAC-IR change-level screening and alcohol dose-dumping assessment"
        onMenuClick={onMenuClick}
      />
      <div className="flex gap-2 overflow-x-auto border-b border-border px-4 pt-3" role="tablist" aria-label="SUPAC screening tools">
        <TabButton active={tab === 'supac'} onClick={() => setTab('supac')} id="supac-tab" controls="supac-panel">
          SUPAC-IR level
        </TabButton>
        <TabButton active={tab === 'alcohol'} onClick={() => setTab('alcohol')} id="alcohol-tab" controls="alcohol-panel">
          Alcohol dose dumping
        </TabButton>
      </div>
      <div className="flex-1 overflow-auto">
        <div hidden={tab !== 'supac'} id="supac-panel" role="tabpanel" aria-labelledby="supac-tab"><SupacClassify /></div>
        <div hidden={tab !== 'alcohol'} id="alcohol-panel" role="tabpanel" aria-labelledby="alcohol-tab"><AlcoholScreening /></div>
      </div>
    </div>
  )
}
function TabButton({
  active,
  onClick,
  id,
  controls,
  children,
}: {
  active: boolean
  onClick: () => void
  id: string
  controls: string
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      id={id}
      role="tab"
      aria-selected={active}
      aria-controls={controls}
      tabIndex={active ? 0 : -1}
      onClick={onClick}
      className={
        'border-b-2 px-3 py-2 text-sm font-medium transition-colors ' +
        (active
          ? 'border-accent text-text'
          : 'border-transparent text-text-muted hover:text-text')
      }
    >
      {children}
    </button>
  )
}

function ScopeBanner() {
  return (
    <div className="mb-2 rounded-sm border border-warning/30 bg-warning/10 p-3 text-sm text-warning">
      <p className="font-semibold">Screening scope</p>
      <p className="mt-1">
        This is SUPAC-IR screening only. It does not replace full SUPAC guidance
        interpretation, regulatory filing strategy, cumulative multi-component
        totals, site/scale/equipment change assessment, or qualified CMC judgement.
      </p>
    </div>
  )
}

function SupacClassify() {
  const [category, setCategory] = useState<SupacComponentCategory>('filler')
  const [changePct, setChangePct] = useState(4.0)

  const request = useMemo<SupacClassifyRequest>(
    () => ({ component_category: category, change_pct: changePct }),
    [category, changePct],
  )

  const mutation = useMutation<SupacClassifyResponse, Error>({
    mutationFn: () => classifySupac(request),
  })
  const result = mutation.data
  const canRun = changePct >= 0 && !mutation.isPending

  useRunShortcut(mutation.mutate, canRun)

  return (
    <AnalysisShell resultKey={Boolean(result)}>
      <div className="flex flex-col gap-5">
        <ScopeBanner />
        <section>
          <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
            1. Component change
          </h3>
          <div className="space-y-2.5">
            <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">
              Excipient function
              <select
                aria-label="Excipient function"
                value={category}
                onChange={(event) => {
                  setCategory(event.target.value as SupacComponentCategory)
                  mutation.reset()
                }}
                className="w-56 rounded-sm border border-border-2 bg-surface-2 px-2.5 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
              >
                {COMPONENT_OPTIONS.map((opt) => (
                  <option key={opt.value} value={opt.value}>
                    {opt.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">
              Absolute change (% total weight)
              <input
                aria-label="Change percent"
                type="number"
                min="0"
                step="0.05"
                value={changePct}
                onChange={(event) => {
                  setChangePct(Number(event.target.value))
                  mutation.reset()
                }}
                className="w-28 rounded-sm border border-border-2 bg-surface-2 px-2.5 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
              />
            </label>
          </div>
        </section>

        <Button
          size="lg"
          className="w-full"
          onClick={() => mutation.mutate()}
          disabled={!canRun}
          loading={mutation.isPending}
        >
          {mutation.isPending ? 'Classifying...' : 'Classify SUPAC-IR level'}
        </Button>
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-5">
        {mutation.isError && (
          <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />
        )}
        {mutation.isPending && <LoadingState />}
        {!result && !mutation.isPending && !mutation.isError && (
          <EmptyResults
            icon={ShieldCheck}
            title="No SUPAC screen yet"
            description="Enter the component change, then run the SUPAC-IR level screening."
          />
        )}

        {result && !mutation.isPending && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-text">Screening Level {result.level}</h2>
              <Badge variant={result.level === 1 ? 'success' : result.level === 2 ? 'warning' : 'danger'}>
                Level {result.level}
              </Badge>
            </div>

            <div className="flex flex-wrap gap-3">
              <MetricCard label="Level" value={result.level} highlight />
              <MetricCard label="Change %" value={result.change_pct} />
              <MetricCard label="Function" value={result.component_category} />
            </div>

            <section className="rounded-sm border border-border bg-surface p-4 lg:p-5">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
                Rationale
              </h3>
              <p className="text-sm text-text">{result.rationale}</p>
            </section>

            <section className="rounded-sm border border-border bg-surface p-4 lg:p-5">
              <h3 className="mb-2 text-xs font-semibold uppercase tracking-wider text-text-muted">
                Recommended screening tests
              </h3>
              <ul className="list-disc space-y-1 pl-5 text-sm text-text">
                {result.recommended_tests.map((test) => (
                  <li key={test}>{test}</li>
                ))}
              </ul>
            </section>

            <p className="rounded-sm border border-warning/20 bg-warning/5 p-3 text-sm text-warning">
              {result.scope_note}
            </p>
            <Disclaimer text={result.disclaimer} />
          </>
        )}
      </div>
    </AnalysisShell>
  )
}

function AlcoholScreening() {
  const [controlRows, setControlRows] = useState<PasteDataRow[]>(CONTROL_EXAMPLE)
  const [ethanolRows, setEthanolRows] = useState<PasteDataRow[]>(ETHANOL_EXAMPLE)
  const [threshold, setThreshold] = useState(50.0)

  const controlSamples = useMemo(
    () => controlRows
      .filter((row) => String(row.time ?? '').trim() !== '' || String(row.concentration ?? '').trim() !== '')
      .map((row) => ({ time: Number(row.time), concentration: Number(row.concentration), complete: String(row.time ?? '').trim() !== '' && String(row.concentration ?? '').trim() !== '' })),
    [controlRows],
  )
  const timePoints = controlSamples.map((sample) => sample.time)
  const controlMeans = controlSamples.map((sample) => sample.concentration)
  const ethanolColumns = useMemo<PasteDataColumn[]>(
    () => [
      { key: 'ethanol_pct', label: 'Ethanol %', type: 'number' },
      ...timePoints.map((time, index) => ({
        key: `p${index}`,
        label: `t=${time}`,
        type: 'number' as const,
      })),
    ],
    [timePoints],
  )

  const ethanolProfiles = useMemo(() => {
    return ethanolRows
      .filter(
        (row) =>
          String(row.ethanol_pct ?? '').trim() !== '' ||
          timePoints.some((_, index) => String(row[`p${index}`] ?? '').trim() !== ''),
      )
      .map((row) => ({
        ethanol_pct: Number(row.ethanol_pct),
        means: timePoints.map((_, index) => Number(row[`p${index}`])),
        complete:
          String(row.ethanol_pct ?? '').trim() !== '' &&
          timePoints.every((_, index) => String(row[`p${index}`] ?? '').trim() !== ''),
      }))
  }, [ethanolRows, timePoints])

  const request = useMemo<AlcoholDosingRequest>(
    () => ({
      time_points: timePoints,
      control_means: controlMeans,
      ethanol_profiles: ethanolProfiles.map(({ ethanol_pct, means }) => ({ ethanol_pct, means })),
      f2_threshold: threshold,
      control_label: 'aqueous',
    }),
    [controlMeans, ethanolProfiles, threshold, timePoints],
  )

  const mutation = useMutation<AlcoholDosingResponse, Error>({
    mutationFn: () => assessAlcoholDosing(request),
  })
  const result = mutation.data
  const validTimes = timePoints.every((time, index) => Number.isFinite(time) && time >= 0 && (index === 0 || time > timePoints[index - 1]))
  const validControl = controlSamples.length >= 3 && controlSamples.every((sample) => sample.complete && Number.isFinite(sample.concentration) && sample.concentration >= 0 && sample.concentration <= 100)
  const validProfiles =
    validControl &&
    validTimes &&
    ethanolProfiles.length > 0 &&
    ethanolProfiles.every((profile) => profile.complete && profile.means.length === controlMeans.length && profile.means.every((mean) => Number.isFinite(mean) && mean >= 0 && mean <= 100)) &&
    new Set(ethanolProfiles.map((profile) => profile.ethanol_pct)).size === ethanolProfiles.length &&
    ethanolProfiles.every((profile) => Number.isFinite(profile.ethanol_pct) && profile.ethanol_pct > 0 && profile.ethanol_pct <= 100)
  const canRun = validProfiles && threshold > 0 && !mutation.isPending

  useRunShortcut(mutation.mutate, canRun)

  return (
    <AnalysisShell leftWide resultKey={Boolean(result)}>
      <div className="flex flex-col gap-5">
        <ScopeBanner />
        <section>
          <div className="mb-2.5 flex items-center justify-between gap-3">
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted">
              1. Aqueous control means (% dissolved)
            </h3>
            <Button variant="ghost" size="sm" onClick={() => { setControlRows(CONTROL_EXAMPLE); mutation.reset() }}>
              <RotateCcw size={13} /> Reset
            </Button>
          </div>
          <PasteDataGrid
            columns={[{ key: 'time', label: 'Time (min)', type: 'number' }, { key: 'concentration', label: '% dissolved', type: 'number' }]}
            rows={controlRows}
            onChange={(nextRows) => { setControlRows(nextRows); mutation.reset() }}
            filename="control_profile.csv"
            hint="Mean percent dissolved at each time point."
          />
        </section>

        <section>
          <h3 className="mb-2.5 text-xs font-semibold uppercase tracking-wider text-text-muted">
            2. Ethanol media means (% dissolved)
          </h3>
          <PasteDataGrid
            columns={ethanolColumns}
            rows={ethanolRows}
            onChange={(nextRows) => { setEthanolRows(nextRows); mutation.reset() }}
            filename="ethanol_profiles.csv"
            hint="One row per ethanol medium. Columns are generated from the control time grid."
          />
        </section>

        <label className="flex items-center justify-between gap-3 text-sm font-semibold text-text">
          f2 threshold
          <input
            aria-label="f2 threshold"
            type="number"
            min="0.001"
            step="1"
            value={threshold}
            onChange={(event) => { setThreshold(Number(event.target.value)); mutation.reset() }}
            className="w-24 rounded-sm border border-border-2 bg-surface-2 px-2.5 py-1.5 text-sm text-text focus:border-accent focus:outline-none"
          />
        </label>

        <Button
          size="lg"
          className="w-full"
          onClick={() => mutation.mutate()}
          disabled={!canRun}
          loading={mutation.isPending}
        >
          {mutation.isPending ? 'Assessing...' : 'Assess alcohol dose dumping'}
        </Button>
        {!validProfiles && (
          <p className="text-center text-xs text-danger">
            Enter at least three complete, increasing control time points and complete unique ethanol profiles with values from 0 to 100.
          </p>
        )}
      </div>

      <div className="flex min-w-0 flex-1 flex-col gap-5">
        {mutation.isError && (
          <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />
        )}
        {mutation.isPending && <LoadingState />}
        {!result && !mutation.isPending && !mutation.isError && (
          <EmptyResults
            icon={ShieldCheck}
            title="No alcohol screen yet"
            description="Enter control and ethanol dissolution profiles, then assess dose dumping."
          />
        )}

        {result && !mutation.isPending && (
          <>
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 className="text-lg font-bold text-text">Alcohol dose-dumping screen</h2>
              <Badge variant={result.overall_pass ? 'success' : 'danger'}>
                {result.overall_pass ? 'Pass (regulatory f2)' : 'Fail (regulatory f2)'}
              </Badge>
            </div>

            <div className="flex flex-wrap gap-3">
              {Object.entries(result.f2_by_ethanol_pct).map(([pct, f2]) => (
                <MetricCard
                  key={pct}
                  label={`f2 @ ${pct}% EtOH`}
                  value={f2}
                  highlight={f2 >= result.f2_threshold}
                />
              ))}
              <MetricCard label="Threshold" value={result.f2_threshold} />
            </div>

            <p className="rounded-sm border border-warning/20 bg-warning/5 p-3 text-sm text-warning">
              {result.scope_note}
            </p>
            <Disclaimer text={result.disclaimer} />
          </>
        )}
      </div>
    </AnalysisShell>
  )
}

function LoadingState() {
  return (
    <div className="space-y-5">
      <div className="flex flex-wrap gap-3">
        {[1, 2, 3].map((item) => <Skeleton key={item} className="h-24 w-36 rounded-sm" />)}
      </div>
      <Skeleton className="h-40 w-full rounded-sm" />
    </div>
  )
}
