import { useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { PasteDataGrid, type PasteDataColumn, type PasteDataRow } from '@/components/shared/PasteDataGrid'
import { Button } from '@/components/ui/Button'
import { Badge } from '@/components/ui/Badge'
import { Select as UiSelect } from '@/components/ui/Select'
import { analyzeIvIvc, downloadIvIvcReport } from '@/lib/api'
import { useRunShortcut } from '@/lib/useRunShortcut'
import type { IvIvcResponse } from '@/lib/types'

const IVIVC_METHODS = ['wagner_nelson', 'loo_riegelman'] as const
type IvIvcMethod = (typeof IVIVC_METHODS)[number]

const IN_VIVO_COLUMNS: PasteDataColumn[] = [
  { key: 'time', label: 'Time (h)', type: 'number' },
  { key: 'conc', label: 'Concentration', type: 'number' },
]

const DISSOLUTION_COLUMNS: PasteDataColumn[] = [
  { key: 'time', label: 'Time (min)', type: 'number' },
  { key: 'pct_dissolved', label: '% Dissolved', type: 'number' },
]

const IV_UIR_COLUMNS: PasteDataColumn[] = [
  { key: 'time', label: 'Time (h)', type: 'number' },
  { key: 'conc', label: 'Concentration', type: 'number' },
]

const EXAMPLE_IN_VIVO_ROWS: PasteDataRow[] = [
  { time: 0.5, conc: 1.5 },
  { time: 1, conc: 3.2 },
  { time: 1.5, conc: 4.8 },
  { time: 2, conc: 6.0 },
  { time: 3, conc: 7.0 },
  { time: 4, conc: 7.0 },
  { time: 6, conc: 5.5 },
  { time: 8, conc: 3.8 },
  { time: 12, conc: 2.0 },
  { time: 18, conc: 0.8 },
  { time: 24, conc: 0.3 },
]

const EXAMPLE_DISSOLUTION_ROWS: PasteDataRow[] = [
  { time: 5, pct_dissolved: 5 },
  { time: 10, pct_dissolved: 15 },
  { time: 20, pct_dissolved: 35 },
  { time: 30, pct_dissolved: 55 },
  { time: 45, pct_dissolved: 75 },
  { time: 60, pct_dissolved: 88 },
  { time: 90, pct_dissolved: 97 },
  { time: 120, pct_dissolved: 100 },
]

const EXAMPLE_IV_UIR_ROWS: PasteDataRow[] = [
  { time: 0.25, conc: 10.0 },
  { time: 0.5, conc: 8.5 },
  { time: 1, conc: 6.5 },
  { time: 2, conc: 4.5 },
  { time: 3, conc: 3.2 },
  { time: 4, conc: 2.2 },
  { time: 6, conc: 1.0 },
  { time: 8, conc: 0.45 },
  { time: 12, conc: 0.1 },
]

function rowsToNumberArrays(rows: PasteDataRow[], timeKey: string, valueKey: string) {
  const valid = rows.filter(
    (r) =>
      String(r[timeKey] ?? '').trim() !== '' &&
      String(r[valueKey] ?? '').trim() !== '',
  )
  return {
    times: valid.map((r) => Number(r[timeKey])),
    values: valid.map((r) => Number(r[valueKey])),
  }
}

export default function IvIvcPage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [inVivoRows, setInVivoRows] = useState<PasteDataRow[]>(EXAMPLE_IN_VIVO_ROWS)
  const [dissolutionRows, setDissolutionRows] = useState<PasteDataRow[]>(EXAMPLE_DISSOLUTION_ROWS)
  const [ivUirRows, setIvUirRows] = useState<PasteDataRow[]>(EXAMPLE_IV_UIR_ROWS)
  const [method, setMethod] = useState<IvIvcMethod>('wagner_nelson')
  const [kel, setKel] = useState<string>('0.12')
  const [k12, setK12] = useState<string>('')
  const [k21, setK21] = useState<string>('')
  const [doseDiss, setDoseDiss] = useState<string>('')
  const [doseIv, setDoseIv] = useState<string>('')
  const [studyLabel, setStudyLabel] = useState<string>('')

  const req = useMemo(() => {
    const inVivo = rowsToNumberArrays(inVivoRows, 'time', 'conc')
    const dissolution = rowsToNumberArrays(dissolutionRows, 'time', 'pct_dissolved')
    const ivUir = rowsToNumberArrays(ivUirRows, 'time', 'conc')
    return {
      in_vivo_times: inVivo.times,
      in_vivo_concs: inVivo.values,
      dissolution_times: dissolution.times,
      dissolution_pct: dissolution.values,
      iv_uir_times: ivUir.times,
      iv_uir_concs: ivUir.values,
      method,
      kel: kel.trim() !== '' ? Number(kel) : null,
      k12: method === 'loo_riegelman' && k12.trim() !== '' ? Number(k12) : null,
      k21: method === 'loo_riegelman' && k21.trim() !== '' ? Number(k21) : null,
      dose_diss: doseDiss.trim() !== '' ? Number(doseDiss) : null,
      dose_iv: doseIv.trim() !== '' ? Number(doseIv) : null,
      study_label: studyLabel,
      dissolution_time_unit: 'minutes' as const,
    }
  }, [inVivoRows, dissolutionRows, ivUirRows, method, kel, k12, k21, doseDiss, doseIv, studyLabel])

  const [runSnapshot, setRunSnapshot] = useState<typeof req | null>(null)

  function loadExample() {
    setInVivoRows(EXAMPLE_IN_VIVO_ROWS)
    setDissolutionRows(EXAMPLE_DISSOLUTION_ROWS)
    setIvUirRows(EXAMPLE_IV_UIR_ROWS)
    setMethod('wagner_nelson')
    setKel('0.12')
    setK12('')
    setK21('')
    setDoseDiss('')
    setDoseIv('')
    setStudyLabel('Example IR tablet')
    setRunSnapshot(null)
    mutation.reset()
  }

  const mutation = useMutation<IvIvcResponse, Error>({
    mutationFn: () => analyzeIvIvc(req),
    onSuccess: () => {
      setRunSnapshot(JSON.parse(JSON.stringify(req)) as typeof req)
    },
  })

  const result = mutation.data
  const resultsStale =
    Boolean(result) &&
    (runSnapshot === null || JSON.stringify(runSnapshot) !== JSON.stringify(req))

  const canRun =
    inVivoRows.some((r) => String(r.time ?? '').trim() !== '') &&
    dissolutionRows.some((r) => String(r.time ?? '').trim() !== '') &&
    ivUirRows.some((r) => String(r.time ?? '').trim() !== '') &&
    kel.trim() !== '' &&
    !mutation.isPending

  useRunShortcut(mutation.mutate, canRun)

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="IVIVC Level A"
        subtitle="In Vitro-In Vivo Correlation analysis using Wagner-Nelson or Loo-Riegelman deconvolution"
        onMenuClick={onMenuClick}
      />

      <AnalysisShell leftWide resultKey={Boolean(result)}>
        {/* Left panel */}
        <div>
          <div className="flex flex-col gap-4">
            {/* Step 1: In Vivo PK Data */}
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                1. In Vivo PK Data
              </h3>
              <PasteDataGrid
                columns={IN_VIVO_COLUMNS}
                rows={inVivoRows}
                onChange={(rows) => {
                  setInVivoRows(rows)
                  mutation.reset()
                }}
                filename="in_vivo_pk.csv"
                hint="Paste in vivo plasma concentration-time data (time in hours)."
              />
            </section>

            {/* Step 2: Dissolution Data */}
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                2. Dissolution Data
              </h3>
              <PasteDataGrid
                columns={DISSOLUTION_COLUMNS}
                rows={dissolutionRows}
                onChange={(rows) => {
                  setDissolutionRows(rows)
                  mutation.reset()
                }}
                filename="dissolution.csv"
                hint="Paste cumulative percent dissolved at each time point (time in minutes)."
              />
            </section>

            {/* Step 3: IV Unit Impulse Response */}
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                3. IV Unit Impulse Response
              </h3>
              <PasteDataGrid
                columns={IV_UIR_COLUMNS}
                rows={ivUirRows}
                onChange={(rows) => {
                  setIvUirRows(rows)
                  mutation.reset()
                }}
                filename="iv_uir.csv"
                hint="Paste IV plasma concentration-time data for deconvolution (time in hours)."
              />
            </section>

            {/* Step 4: Options */}
            <section>
              <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2.5">
                4. Options
              </h3>
              <div className="space-y-2.5">
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">Method</span>
                  <UiSelect
                    value={method}
                    onChange={(e) => {
                      setMethod(e.target.value as IvIvcMethod)
                      mutation.reset()
                    }}
                    className="min-w-[180px]"
                  >
                    {IVIVC_METHODS.map((m) => (
                      <option key={m} value={m}>
                        {m === 'wagner_nelson' ? 'Wagner-Nelson' : 'Loo-Riegelman'}
                      </option>
                    ))}
                  </UiSelect>
                </div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">
                    kel (h<sup>-1</sup>, optional)
                  </span>
                  <input
                    type="number"
                    value={kel}
                    onChange={(e) => setKel(e.target.value)}
                    placeholder="auto"
                    className="w-28 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                  />
                </div>
                {method === 'loo_riegelman' && (
                  <>
                    <div className="flex justify-between items-center gap-3">
                      <span className="text-sm font-semibold text-text shrink-0">
                        k12 (h<sup>-1</sup>, optional)
                      </span>
                      <input
                        type="number"
                        value={k12}
                        onChange={(e) => setK12(e.target.value)}
                        placeholder="auto"
                        className="w-28 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                      />
                    </div>
                    <div className="flex justify-between items-center gap-3">
                      <span className="text-sm font-semibold text-text shrink-0">
                        k21 (h<sup>-1</sup>, optional)
                      </span>
                      <input
                        type="number"
                        value={k21}
                        onChange={(e) => setK21(e.target.value)}
                        placeholder="auto"
                        className="w-28 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                      />
                    </div>
                  </>
                )}
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">
                    Dose (dissolution, optional)
                  </span>
                  <input
                    type="number"
                    value={doseDiss}
                    onChange={(e) => setDoseDiss(e.target.value)}
                    placeholder="optional"
                    className="w-28 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                  />
                </div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">
                    Dose (IV, optional)
                  </span>
                  <input
                    type="number"
                    value={doseIv}
                    onChange={(e) => setDoseIv(e.target.value)}
                    placeholder="optional"
                    className="w-28 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                  />
                </div>
                <div className="flex justify-between items-center gap-3">
                  <span className="text-sm font-semibold text-text shrink-0">Study label</span>
                  <input
                    type="text"
                    value={studyLabel}
                    onChange={(e) => setStudyLabel(e.target.value)}
                    placeholder="optional"
                    className="w-40 bg-surface-2 border border-border-2 rounded-sm px-2.5 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent"
                  />
                </div>
              </div>
            </section>

            <Button
              type="button"
              variant="secondary"
              onClick={loadExample}
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
              {mutation.isPending ? 'Analyzing...' : 'Run IVIVC'}
            </Button>
          </div>
        </div>

        {/* Right panel */}
        <div className="flex-1 min-w-0 flex flex-col gap-5">
          {mutation.isError && (
            <ErrorBanner message={mutation.error.message} onDismiss={() => mutation.reset()} />
          )}

          {result && !mutation.isPending && (
            <>
              {/* Pass/fail badge */}
              <div className="flex items-center gap-3 flex-wrap">
                <Badge variant={result.overall_pass ? 'success' : 'danger'}>
                  {result.overall_pass ? 'IVIVC Acceptable' : 'IVIVC Not Acceptable'}
                </Badge>
                {result.study_label && (
                  <span className="text-sm text-text-muted">{result.study_label}</span>
                )}
              </div>

              {/* Metrics */}
              <div className="flex gap-3 flex-wrap">
                <MetricCard
                  label="Levy R2"
                  value={result.levy_r_squared}
                  highlight={result.levy_r_squared != null && result.levy_r_squared >= 0.9}
                />
                <MetricCard
                  label="%PE Cmax"
                  value={result.pe_cmax}
                  unit="%"
                />
                <MetricCard
                  label="%PE AUC"
                  value={result.pe_auc}
                  unit="%"
                />
                <MetricCard
                  label="Mean |%PE|"
                  value={result.mean_abs_pe}
                  unit="%"
                />
              </div>

              {/* Charts side by side */}
              <div className="flex flex-col xl:flex-row gap-5">
                {/* Fraction Absorbed vs Dissolved */}
                <div className="flex-1 bg-surface border border-border rounded-sm p-4 lg:p-5 min-w-0">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
                    Fraction Absorbed vs Dissolved
                  </h3>
                  <PKChart
                    series={[
                      {
                        name: 'Fa (in vivo)',
                        times: result.times,
                        concs: result.fa,
                        color: '#5e6ad2',
                      },
                      {
                        name: 'F dissolved (in vitro)',
                        times: result.ivt_times,
                        concs: result.ivt_fraction,
                        color: '#3dd68c',
                        dashed: true,
                      },
                    ]}
                    xLabel="Time (h)"
                    yLabel="Fraction"
                  />
                </div>

                {/* Predicted vs Observed */}
                <div className="flex-1 bg-surface border border-border rounded-sm p-4 lg:p-5 min-w-0">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-3">
                    Predicted vs Observed
                  </h3>
                  <PKChart
                    series={[
                      {
                        name: 'Observed',
                        times: result.times,
                        concs: result.concentrations,
                        color: '#5e6ad2',
                      },
                      {
                        name: 'Predicted',
                        times: result.predicted_times,
                        concs: result.predicted_concs,
                        color: '#f0a731',
                        dashed: true,
                      },
                    ]}
                    xLabel="Time (h)"
                    yLabel="Concentration"
                  />
                </div>
              </div>

              {resultsStale && (
                <div className="rounded-sm border border-warning/30 bg-warning/10 p-3 text-warning text-sm">
                  <p className="font-semibold mb-1">Results are stale</p>
                  <p>
                    Inputs or options changed after the last run. Re-run IVIVC before
                    downloading a report so the visible results and the report match.
                  </p>
                </div>
              )}
              {resultsStale ? (
                <p className="text-sm text-text-muted">
                  Report download disabled until you re-run with the current options.
                </p>
              ) : (
                <DownloadReportButton
                  formats={['html', 'markdown', 'pdf', 'docx']}
                  onDownload={(fmt) => downloadIvIvcReport(runSnapshot!, fmt)}
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
