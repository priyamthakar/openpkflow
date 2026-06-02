import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useOutletContext } from 'react-router-dom'
import { TopBar } from '@/components/layout/TopBar'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
import { AnalysisShell } from '@/components/shared/AnalysisShell'
import { Skeleton } from '@/components/ui/Skeleton'
import { simulate, downloadSimReport } from '@/lib/api'
import type { SimResponse } from '@/lib/types'

type ModelType = '1cmt' | '2cmt'
type Route = 'oral' | 'iv_bolus' | 'iv_infusion'

interface SliderDef {
  key: string
  label: string
  min: number
  max: number
  step: number
  defaultValue: number
}

function getSliders(modelType: ModelType, route: Route): SliderDef[] {
  const dose = { key: 'dose', label: 'Dose (mg)', min: 1, max: 1000, step: 1, defaultValue: 100 }
  const tau = { key: 'tau', label: 'Tau (h)', min: 1, max: 72, step: 1, defaultValue: 12 }
  const nDoses = { key: 'n_doses', label: 'Number of doses', min: 1, max: 20, step: 1, defaultValue: 1 }
  const tStop = { key: 't_stop', label: 'Simulate until (h)', min: 6, max: 360, step: 6, defaultValue: 48 }
  const regimen = [dose, tau, nDoses, tStop]

  if (modelType === '1cmt') {
    if (route === 'oral') {
      return [
        { key: 'CL_F', label: 'CL/F (L/h)', min: 0.1, max: 100, step: 0.1, defaultValue: 5 },
        { key: 'Vz_F', label: 'Vz/F (L)', min: 1, max: 500, step: 1, defaultValue: 50 },
        { key: 'ka', label: 'ka (h^-1)', min: 0.01, max: 10, step: 0.01, defaultValue: 1.2 },
        ...regimen,
      ]
    }
    return [
      { key: 'CL', label: 'CL (L/h)', min: 0.1, max: 100, step: 0.1, defaultValue: 5 },
      { key: 'Vz', label: 'Vz (L)', min: 1, max: 500, step: 1, defaultValue: 50 },
      ...(route === 'iv_infusion'
        ? [{ key: 't_inf', label: 'Infusion duration (h)', min: 0.1, max: 24, step: 0.1, defaultValue: 1 }]
        : []),
      ...regimen,
    ]
  }
  if (route === 'oral') {
    return [
      { key: 'CL_F', label: 'CL/F (L/h)', min: 0.1, max: 100, step: 0.1, defaultValue: 5 },
      { key: 'V1_F', label: 'V1/F (L)', min: 1, max: 300, step: 1, defaultValue: 20 },
      { key: 'Q', label: 'Q (L/h)', min: 0.1, max: 50, step: 0.1, defaultValue: 2 },
      { key: 'V2', label: 'V2 (L)', min: 1, max: 500, step: 1, defaultValue: 30 },
      { key: 'ka', label: 'ka (h^-1)', min: 0.01, max: 10, step: 0.01, defaultValue: 1.2 },
      ...regimen,
    ]
  }
  return [
    { key: 'CL', label: 'CL (L/h)', min: 0.1, max: 100, step: 0.1, defaultValue: 5 },
    { key: 'V1', label: 'V1 (L)', min: 1, max: 300, step: 1, defaultValue: 20 },
    { key: 'Q', label: 'Q (L/h)', min: 0.1, max: 50, step: 0.1, defaultValue: 2 },
    { key: 'V2', label: 'V2 (L)', min: 1, max: 500, step: 1, defaultValue: 30 },
    ...(route === 'iv_infusion'
      ? [{ key: 't_inf', label: 'Infusion duration (h)', min: 0.1, max: 24, step: 0.1, defaultValue: 1 }]
      : []),
    ...regimen,
  ]
}

function buildRequest(modelType: ModelType, route: Route, vals: Record<string, number>) {
  const { dose, tau, n_doses, t_stop, t_inf, ...params } = vals
  return {
    model_type: modelType,
    route,
    params,
    regimen: { amount: dose, tau, n_doses: Math.round(n_doses), t_start: 0.0, t_inf: t_inf ?? null },
    times: { start: 0, stop: t_stop, n: 300 },
  }
}

function defaultValues(modelType: ModelType, route: Route) {
  const defaults: Record<string, number> = {}
  getSliders(modelType, route).forEach((s) => {
    defaults[s.key] = s.defaultValue
  })
  return defaults
}

export default function SimPage() {
  const { onMenuClick } = useOutletContext<{ onMenuClick: () => void }>()
  const [modelType, setModelType] = useState<ModelType>('1cmt')
  const [route, setRoute] = useState<Route>('oral')
  const [vals, setVals] = useState<Record<string, number>>(() => defaultValues('1cmt', 'oral'))
  const [req, setReq] = useState<object | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    if (Object.keys(vals).length === 0) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setReq(buildRequest(modelType, route, vals))
    }, 250)
    return () => {
      if (debounceRef.current) clearTimeout(debounceRef.current)
    }
  }, [vals, modelType, route])

  const { data, isFetching, isError, error } = useQuery<SimResponse, Error>({
    queryKey: ['sim', req],
    queryFn: () => simulate(req!),
    enabled: req !== null,
    retry: false,
  })

  function setVal(key: string, value: number) {
    setVals((v) => ({ ...v, [key]: value }))
  }

  function changeModel(next: ModelType) {
    setModelType(next)
    setVals(defaultValues(next, route))
  }

  function changeRoute(next: Route) {
    setRoute(next)
    setVals(defaultValues(modelType, next))
  }

  return (
    <div className="flex flex-col h-full">
      <TopBar
        title="PK Simulation Playground"
        subtitle="Drag sliders and the curve updates live"
        onMenuClick={onMenuClick}
      />

      <AnalysisShell resultKey={Boolean(data)}>
        {/* Control panel */}
        <div className="flex flex-col gap-4">
          {/* Model type chips */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">Model</h3>
            <div className="flex gap-2 flex-wrap">
              {(['1cmt', '2cmt'] as const).map((m) => (
                <Chip key={m} active={modelType === m} onClick={() => changeModel(m)} label={m} />
              ))}
            </div>
          </div>

          {/* Route chips */}
          <div>
            <h3 className="text-xs font-semibold uppercase tracking-wider text-text-muted mb-2">Route</h3>
            <div className="flex gap-2 flex-wrap">
              {(['oral', 'iv_bolus', 'iv_infusion'] as const).map((r) => (
                <Chip key={r} active={route === r} onClick={() => changeRoute(r)} label={r.replace('_', ' ')} />
              ))}
            </div>
          </div>

          {/* Sliders */}
          <div className="space-y-1">
            {getSliders(modelType, route).map((s) => (
              <SliderRow
                key={s.key}
                def={s}
                value={vals[s.key] ?? s.defaultValue}
                onChange={(v) => setVal(s.key, v)}
              />
            ))}
          </div>

          {/* Parameter grid */}
          <ParameterGrid
            sliders={getSliders(modelType, route)}
            vals={vals}
            onChange={setVal}
            onPasteValues={(next) => setVals((current) => ({ ...current, ...next }))}
          />
        </div>

        {/* Chart + metrics */}
        <div className="flex-1 min-w-0 flex flex-col gap-5">
          {isError && <ErrorBanner message={(error as Error).message} />}

          {isFetching && !data && (
            <div className="space-y-5">
              <div className="flex gap-3 flex-wrap">
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
                <Skeleton className="h-24 w-36 rounded-sm" />
              </div>
              <Skeleton className="h-80 w-full rounded-sm" />
            </div>
          )}

          {data && (
            <>
              <div className="flex gap-3 flex-wrap">
                <MetricCard label="Cmax" value={data.Cmax} highlight />
                <MetricCard label="Tmax" value={data.Tmax} unit="h" />
                <MetricCard label="Cmin" value={data.Cmin} />
                <MetricCard label="Clast" value={data.Clast} />
              </div>

              <div className="bg-surface border border-border rounded-sm p-4 lg:p-5 relative">
                {isFetching && (
                  <div className="absolute top-3 right-4 text-xs text-text-dim flex items-center gap-1.5">
                    <span className="w-2 h-2 bg-accent rounded-full animate-pulse" />
                    updating...
                  </div>
                )}
                <PKChart
                  series={[{ name: 'Concentration', times: data.times, concs: data.concs }]}
                  xLabel="Time (h)"
                  yLabel="Concentration"
                  doseTimes={data.dose_times}
                />
              </div>

              <InterpretationPanel
                modelType={modelType}
                route={route}
                vals={vals}
                data={data}
              />

              {data.warnings.length > 0 && (
                <div className="text-sm text-warning space-y-0.5">
                  {data.warnings.map((w, i) => (
                    <p key={i}>Warning: {w}</p>
                  ))}
                </div>
              )}

              <DownloadReportButton onDownload={(fmt) => downloadSimReport(req!, fmt)} />
              <Disclaimer text={data.disclaimer} />
            </>
          )}
        </div>
      </AnalysisShell>
    </div>
  )
}

function Chip({ active, onClick, label }: { active: boolean; onClick: () => void; label: string }) {
  return (
    <button
      onClick={onClick}
      className={`px-3 py-1.5 rounded-sm text-sm font-medium border transition-all duration-150
        focus:outline-none focus-visible:ring-2 focus-visible:ring-accent/40
        ${
          active
            ? 'bg-accent-muted border-accent/40 text-accent'
            : 'bg-surface-2 border-border text-text hover:border-border-2'
        }`}
    >
      {label}
    </button>
  )
}

function SliderRow({ def, value, onChange }: { def: SliderDef; value: number; onChange: (v: number) => void }) {
  return (
    <div className="group flex items-center gap-2.5 py-1 pl-2.5 -ml-2.5 border-l-2 border-l-transparent hover:border-l-accent/30 transition-colors rounded-r-md">
      <div className="flex-1 min-w-0">
        <div className="flex justify-between items-baseline mb-0.5">
          <span className="text-sm font-semibold text-text transition-colors truncate">
            {def.label}
          </span>
        </div>
        <input
          type="range"
          min={def.min}
          max={def.max}
          step={def.step}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          className="w-full h-1.5 bg-surface-2 rounded-full appearance-none cursor-pointer accent-accent hover:accent-accent-hover"
        />
      </div>
      <input
        type="number"
        value={value}
        min={def.min}
        max={def.max}
        step={def.step}
        onChange={(e) => onChange(Number(e.target.value))}
        className="w-16 text-right bg-surface-2 border border-border-2 rounded-sm px-2 py-1 text-xs font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent tabular-nums"
      />
    </div>
  )
}

function ParameterGrid({
  sliders,
  vals,
  onChange,
  onPasteValues,
}: {
  sliders: SliderDef[]
  vals: Record<string, number>
  onChange: (key: string, value: number) => void
  onPasteValues: (values: Record<string, number>) => void
}) {
  function handlePaste(e: React.ClipboardEvent<HTMLDivElement>) {
    const text = e.clipboardData.getData('text')
    const parsed = parsePastedParameters(text, sliders)
    if (Object.keys(parsed).length === 0) return
    e.preventDefault()
    onPasteValues(parsed)
  }

  function copyCsv() {
    const csv = ['parameter,value', ...sliders.map((s) => `${s.key},${vals[s.key] ?? s.defaultValue}`)].join('\n')
    void navigator.clipboard.writeText(csv)
  }

  return (
    <section
      onPaste={handlePaste}
      className="bg-surface border border-border rounded-sm overflow-hidden mt-2"
    >
      <div className="flex justify-between items-center px-3 py-2.5 border-b border-border">
        <h3 className="text-sm font-semibold text-text">Parameter grid</h3>
        <button
          type="button"
          onClick={copyCsv}
          className="px-2.5 py-1 text-xs border border-border-2 bg-surface-2 text-text rounded-sm hover:border-accent transition-colors"
        >
          Copy CSV
        </button>
      </div>
      <table className="w-full border-collapse text-sm">
        <thead>
          <tr>
            <th className="px-2.5 py-2 bg-surface-2 text-text text-left border-b border-border font-semibold text-xs">
              Parameter
            </th>
            <th className="px-2.5 py-2 bg-surface-2 text-text text-left border-b border-border font-semibold text-xs">
              Value
            </th>
          </tr>
        </thead>
        <tbody>
          {sliders.map((s) => (
            <tr key={s.key}>
              <td className="px-2.5 py-2 border-b border-border">
                <div className="text-text font-semibold text-xs">{s.key}</div>
                <div className="text-text-muted text-[12px] font-medium">{s.label}</div>
              </td>
              <td className="px-2.5 py-2 border-b border-border">
                <input
                  type="number"
                  value={vals[s.key] ?? s.defaultValue}
                  min={s.min}
                  max={s.max}
                  step={s.step}
                  onChange={(e) => onChange(s.key, Number(e.target.value))}
                  className="w-full bg-surface-2 border border-border-2 rounded-sm px-2 py-1.5 text-sm font-semibold text-text focus:outline-none focus:ring-2 focus:ring-accent/30 focus:border-accent tabular-nums"
                />
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      <div className="px-3 py-2 text-text-muted text-xs border-t border-border">
        Paste two columns from Excel: parameter name, then value.
      </div>
    </section>
  )
}

function parsePastedParameters(text: string, sliders: SliderDef[]) {
  const allowed = new Map<string, string>()
  sliders.forEach((s) => {
    allowed.set(s.key.toLowerCase(), s.key)
    allowed.set(s.label.toLowerCase(), s.key)
    allowed.set(s.label.split(' ')[0].toLowerCase(), s.key)
  })

  const next: Record<string, number> = {}
  text
    .trim()
    .split(/\r?\n/)
    .forEach((line) => {
      const cells = line.split(/\t|,/).map((c) => c.trim()).filter(Boolean)
      if (cells.length < 2) return
      const key = allowed.get(cells[0].toLowerCase())
      const value = Number(cells[1])
      if (key && Number.isFinite(value)) next[key] = value
    })
  return next
}

function InterpretationPanel({
  modelType,
  route,
  vals,
  data,
}: {
  modelType: ModelType
  route: Route
  vals: Record<string, number>
  data: SimResponse
}) {
  const defaultVals = defaultValues(modelType, route)
  const activeLevers = getActiveLevers(vals, defaultVals)
  const tailText = data.Clast > data.Cmax * 0.2 ? 'Slow washout' : 'Mostly cleared'

  return (
    <div className="bg-surface border border-border rounded-sm p-4 lg:p-5">
      <h3 className="text-base font-semibold text-text mb-2">Interpretation</h3>
      <p className="text-sm text-text-muted leading-relaxed mb-3">
        Peak at {data.Tmax.toFixed(1)} h. {tailText} by the end.
      </p>
      <div className="flex gap-2 flex-wrap">
        {(activeLevers.length > 0 ? activeLevers : parameterGuidance(modelType, route).slice(0, 4)).map((item) => (
          <span
            key={item}
            className="bg-surface-2 border border-border rounded-full text-text-muted text-xs font-semibold px-3 py-1.5"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  )
}

function getActiveLevers(vals: Record<string, number>, defaults: Record<string, number>) {
  return Object.entries(vals)
    .filter(([key, value]) => key in defaults && Math.abs(value - defaults[key]) > 1e-9)
    .map(([key, value]) => {
      const direction = value > defaults[key] ? 'higher' : 'lower'
      return `${labelFor(key)} ${direction}: ${effectFor(key, value > defaults[key])}`
    })
    .slice(0, 4)
}

function parameterGuidance(modelType: ModelType, route: Route) {
  const keys = getSliders(modelType, route).map((s) => s.key)
  return keys.map((key) => `${labelFor(key)} up: ${effectFor(key, true)}`).slice(0, 4)
}

function labelFor(key: string) {
  const labels: Record<string, string> = {
    CL: 'clearance',
    CL_F: 'apparent clearance',
    Vz: 'volume',
    Vz_F: 'apparent volume',
    V1: 'central volume',
    V1_F: 'apparent central volume',
    Q: 'intercompartmental clearance',
    V2: 'peripheral volume',
    ka: 'absorption rate',
    dose: 'dose',
    tau: 'dosing interval',
    n_doses: 'number of doses',
    t_stop: 'simulation window',
    t_inf: 'infusion duration',
  }
  return labels[key] ?? key
}

function effectFor(key: string, increased: boolean) {
  const up: Record<string, string> = {
    CL: 'lower exposure',
    CL_F: 'lower exposure',
    Vz: 'lower peak, longer tail',
    Vz_F: 'lower peak, longer tail',
    V1: 'lower early peak',
    V1_F: 'lower early peak',
    Q: 'faster tissue exchange',
    V2: 'longer tail',
    ka: 'earlier peak',
    dose: 'higher curve',
    tau: 'less accumulation',
    n_doses: 'more accumulation',
    t_stop: 'longer view',
    t_inf: 'flatter peak',
  }
  const down: Record<string, string> = {
    CL: 'higher exposure',
    CL_F: 'higher exposure',
    Vz: 'higher peak',
    Vz_F: 'higher peak',
    V1: 'higher early peak',
    V1_F: 'higher early peak',
    Q: 'slower tissue exchange',
    V2: 'shorter tail',
    ka: 'later peak',
    dose: 'lower curve',
    tau: 'more accumulation',
    n_doses: 'less accumulation',
    t_stop: 'shorter view',
    t_inf: 'sharper peak',
  }
  return increased ? up[key] ?? 'profile shifts' : down[key] ?? 'profile shifts'
}
