import { useEffect, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { TopBar } from '@/components/layout/TopBar'
import { PKChart } from '@/components/shared/PKChart'
import { MetricCard } from '@/components/shared/MetricCard'
import { ErrorBanner } from '@/components/shared/ErrorBanner'
import { Disclaimer } from '@/components/shared/Disclaimer'
import { DownloadReportButton } from '@/components/shared/DownloadReportButton'
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
  const tau = { key: 'tau', label: 'Tau / dosing interval (h)', min: 1, max: 72, step: 1, defaultValue: 12 }
  const nDoses = { key: 'n_doses', label: 'Number of doses', min: 1, max: 20, step: 1, defaultValue: 1 }
  const tStop = { key: 't_stop', label: 'Simulate until (h)', min: 6, max: 360, step: 6, defaultValue: 48 }
  const commonRegimen = [dose, tau, nDoses, tStop]

  if (modelType === '1cmt') {
    if (route === 'oral') {
      return [
        { key: 'CL_F', label: 'CL/F (L/h)', min: 0.1, max: 100, step: 0.1, defaultValue: 5 },
        { key: 'Vz_F', label: 'Vz/F (L)', min: 1, max: 500, step: 1, defaultValue: 50 },
        { key: 'ka', label: 'ka (h⁻¹)', min: 0.01, max: 10, step: 0.01, defaultValue: 1.2 },
        ...commonRegimen,
      ]
    }
    return [
      { key: 'CL', label: 'CL (L/h)', min: 0.1, max: 100, step: 0.1, defaultValue: 5 },
      { key: 'Vz', label: 'Vz (L)', min: 1, max: 500, step: 1, defaultValue: 50 },
      ...(route === 'iv_infusion'
        ? [{ key: 't_inf', label: 'Infusion duration (h)', min: 0.1, max: 24, step: 0.1, defaultValue: 1 }]
        : []),
      ...commonRegimen,
    ]
  }
  if (route === 'oral') {
    return [
      { key: 'CL_F', label: 'CL/F (L/h)', min: 0.1, max: 100, step: 0.1, defaultValue: 5 },
      { key: 'V1_F', label: 'V1/F (L)', min: 1, max: 300, step: 1, defaultValue: 20 },
      { key: 'Q', label: 'Q (L/h)', min: 0.1, max: 50, step: 0.1, defaultValue: 2 },
      { key: 'V2', label: 'V2 (L)', min: 1, max: 500, step: 1, defaultValue: 30 },
      { key: 'ka', label: 'ka (h⁻¹)', min: 0.01, max: 10, step: 0.01, defaultValue: 1.2 },
      ...commonRegimen,
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
    ...commonRegimen,
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

export function SimPage() {
  const [modelType, setModelType] = useState<ModelType>('1cmt')
  const [route, setRoute] = useState<Route>('oral')
  const [vals, setVals] = useState<Record<string, number>>({})
  const [req, setReq] = useState<object | null>(null)
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    const defaults: Record<string, number> = {}
    getSliders(modelType, route).forEach((s) => { defaults[s.key] = s.defaultValue })
    setVals(defaults)
  }, [modelType, route])

  useEffect(() => {
    if (Object.keys(vals).length === 0) return
    if (debounceRef.current) clearTimeout(debounceRef.current)
    debounceRef.current = setTimeout(() => {
      setReq(buildRequest(modelType, route, vals))
    }, 250)
    return () => { if (debounceRef.current) clearTimeout(debounceRef.current) }
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

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <TopBar title="PK Simulation Playground" subtitle="Drag sliders — curve updates live" />

      <div style={{ flex: 1, overflowY: 'auto', display: 'flex', padding: 28, gap: 24 }}>
        {/* Control panel */}
        <div style={{ width: 300, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 14 }}>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {(['1cmt', '2cmt'] as const).map((m) => (
              <Chip key={m} active={modelType === m} onClick={() => setModelType(m)}>{m}</Chip>
            ))}
          </div>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {(['oral', 'iv_bolus', 'iv_infusion'] as const).map((r) => (
              <Chip key={r} active={route === r} onClick={() => setRoute(r)}>{r.replace('_', ' ')}</Chip>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 12, marginTop: 4 }}>
            {getSliders(modelType, route).map((s) => (
              <SliderRow
                key={s.key}
                def={s}
                value={vals[s.key] ?? s.defaultValue}
                onChange={(v) => setVal(s.key, v)}
              />
            ))}
          </div>
        </div>

        {/* Chart + metrics */}
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: 20 }}>
          {isError && <ErrorBanner message={(error as Error).message} />}

          {isFetching && !data && (
            <div style={{ color: 'var(--text-dim)', fontSize: 13 }}>Simulating…</div>
          )}

          {data && (
            <>
              <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <MetricCard label="Cmax" value={data.Cmax} unit="conc" highlight />
                <MetricCard label="Tmax" value={data.Tmax} unit="h" />
                <MetricCard label="Cmin" value={data.Cmin} unit="conc" />
                <MetricCard label="Clast" value={data.Clast} unit="conc" />
              </div>

              <div
                style={{
                  background: 'var(--surface)',
                  border: '1px solid var(--border)',
                  borderRadius: 'var(--radius)',
                  padding: 20,
                  position: 'relative',
                }}
              >
                {isFetching && (
                  <div style={{ position: 'absolute', top: 12, right: 16, fontSize: 11, color: 'var(--text-dim)' }}>
                    updating…
                  </div>
                )}
                <PKChart
                  series={[{ name: 'Concentration', times: data.times, concs: data.concs }]}
                  xLabel="Time (h)"
                  yLabel="Concentration"
                  doseTimes={data.dose_times}
                />
              </div>

              {data.warnings.length > 0 && (
                <div style={{ fontSize: 12, color: 'var(--warning)' }}>
                  {data.warnings.map((w, i) => <p key={i}>⚠ {w}</p>)}
                </div>
              )}

              <DownloadReportButton onDownload={(fmt) => downloadSimReport(req!, fmt)} />
              <Disclaimer text={data.disclaimer} />
            </>
          )}
        </div>
      </div>
    </div>
  )
}

function Chip({ active, onClick, children }: { active: boolean; onClick: () => void; children: React.ReactNode }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '5px 12px', borderRadius: 5, fontSize: 12, fontWeight: active ? 600 : 400,
        background: active ? 'var(--accent-muted)' : 'var(--surface-2)',
        color: active ? 'var(--accent)' : 'var(--text-muted)',
        border: `1px solid ${active ? 'rgba(94,106,210,0.4)' : 'var(--border)'}`,
        cursor: 'pointer',
      }}
    >
      {children}
    </button>
  )
}

function SliderRow({ def, value, onChange }: { def: SliderDef; value: number; onChange: (v: number) => void }) {
  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 4 }}>
        <span style={{ fontSize: 11, color: 'var(--text-muted)' }}>{def.label}</span>
        <input
          type="number"
          value={value}
          min={def.min}
          max={def.max}
          step={def.step}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{
            width: 64, background: 'var(--surface-2)', border: '1px solid var(--border-2)',
            borderRadius: 4, color: 'var(--text)', padding: '2px 6px', fontSize: 12, textAlign: 'right',
          }}
        />
      </div>
      <input
        type="range"
        min={def.min}
        max={def.max}
        step={def.step}
        value={value}
        onChange={(e) => onChange(Number(e.target.value))}
        style={{ width: '100%', accentColor: 'var(--accent)', cursor: 'pointer' }}
      />
    </div>
  )
}
