import { useState, useRef } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { cn } from '@/lib/utils'

interface Series {
  name: string
  times: number[]
  concs: number[]
  color?: string
  dashed?: boolean
}

interface Props {
  series: Series[]
  xLabel?: string
  yLabel?: string
  doseTimes?: number[]
  thresholdY?: number
  thresholdLabel?: string
  lambdaZ?: { times: number[]; concs: number[] }
  className?: string
}

export function PKChart({
  series,
  xLabel = 'Time (h)',
  yLabel = 'Concentration',
  doseTimes,
  thresholdY,
  thresholdLabel = '85% threshold',
  lambdaZ,
  className,
}: Props) {
  const [logScale, setLogScale] = useState(false)
  const [hiddenSeries, setHiddenSeries] = useState<Set<string>>(new Set())
  const chartRef = useRef<HTMLDivElement>(null)

  const allTimes = [...new Set(series.flatMap((s) => s.times))].sort((a, b) => a - b)
  const logSafeTimes = logScale ? allTimes.filter((t) => series.every((s) => {
    const idx = s.times.indexOf(t)
    return idx === -1 || s.concs[idx] > 0
  })) : allTimes

  const data = logSafeTimes.map((t) => {
    const row: Record<string, number | null> = { time: t }
    series.forEach((s) => {
      const idx = s.times.indexOf(t)
      const val = idx !== -1 ? s.concs[idx] : null
      row[s.name] = logScale && val != null && val <= 0 ? null : val
    })
    return row
  })

  const COLORS = ['#5e6ad2', '#3dd68c', '#f0a731', '#e5534b', '#a78bfa']

  return (
    <div ref={chartRef} className={cn('relative', className)}>
      <div className="flex justify-end mb-2 gap-1">
        <button
          onClick={() => setLogScale((l) => !l)}
          className={cn(
            'px-2.5 py-1 rounded-sm text-xs font-medium border transition-colors',
            logScale
              ? 'bg-accent-muted border-accent/30 text-accent'
              : 'bg-surface-2 border-border-2 text-text-muted hover:text-text hover:border-border',
          )}
        >
          {logScale ? 'Linear' : 'Semi-log'}
        </button>
      </div>

      {logScale && (
        <p className="text-[11px] text-text-dim mb-1.5">
          Non-positive values are hidden on log scale.
        </p>
      )}

      <ResponsiveContainer width="100%" height={320}>
        <LineChart data={data} margin={{ top: 4, right: 20, bottom: 4, left: 10 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" strokeOpacity={0.6} />
          <XAxis
            dataKey="time"
            tickFormatter={formatAxisTick}
            tick={{ fill: 'var(--text-muted)', fontSize: 13 }}
            label={{
              value: xLabel,
              position: 'insideBottom',
              offset: -4,
              fill: 'var(--text-muted)',
              fontSize: 13,
            }}
          />
          <YAxis
            scale={logScale ? 'log' : 'auto'}
            domain={logScale ? undefined : ([0, 'auto'] as [number, string])}
            tickFormatter={formatAxisTick}
            tick={{ fill: 'var(--text-muted)', fontSize: 13 }}
            label={{
              value: yLabel,
              angle: -90,
              position: 'insideLeft',
              fill: 'var(--text-muted)',
              fontSize: 13,
            }}
          />
          <Tooltip
            content={<ChartTooltip />}
            cursor={{ stroke: 'var(--accent)', strokeOpacity: 0.3, strokeWidth: 1 }}
          />
          {series.length > 1 && (
            <Legend
              wrapperStyle={{ fontSize: 14, color: 'var(--text-muted)' }}
              onClick={(e) => {
                if (!e.dataKey) return
                setHiddenSeries((prev) => {
                  const next = new Set(prev)
                  if (next.has(e.dataKey as string)) next.delete(e.dataKey as string)
                  else next.add(e.dataKey as string)
                  return next
                })
              }}
            />
          )}

          {doseTimes?.map((dt) => (
            <ReferenceLine key={`dose-${dt}`} x={dt} stroke="var(--danger)" strokeDasharray="4 3" strokeOpacity={0.5} />
          ))}

          {thresholdY != null && !logScale && (
            <ReferenceLine
              y={thresholdY}
              stroke="var(--warning)"
              strokeDasharray="4 3"
              label={{ value: thresholdLabel, fill: 'var(--warning)', fontSize: 12 }}
            />
          )}

          {series.map((s, i) => (
            <Line
              key={s.name}
              type="monotone"
              dataKey={s.name}
              stroke={s.color ?? COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              strokeDasharray={s.dashed ? '6 3' : undefined}
              connectNulls={false}
              hide={hiddenSeries.has(s.name)}
              isAnimationActive={true}
              animationDuration={600}
            />
          ))}

          {lambdaZ?.times.map((t, i) => (
            <ReferenceLine key={`lz-${i}`} x={t} stroke="var(--accent)" strokeOpacity={0.5} strokeDasharray="2 2" />
          ))}

        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

function ChartTooltip({
  active,
  payload,
  label,
}: {
  active?: boolean
  payload?: { name?: string; value?: number; color?: string }[]
  label?: number
}) {
  if (!active || !payload) return null
  return (
    <div className="bg-surface border border-border rounded-sm shadow-lg px-3 py-2 text-sm">
      <p className="text-text-muted mb-1 text-xs">Time: {formatAxisTick(label)}h</p>
      {payload
        .filter((entry) => entry.value != null)
        .map((entry) => (
          <p key={entry.name} className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full shrink-0" style={{ background: entry.color }} />
            <span className="text-text">{entry.name}:</span>
            <span className="font-mono font-medium tabular-nums">
              {formatMetric(entry.value)}
            </span>
          </p>
        ))}
    </div>
  )
}

function formatAxisTick(value: unknown) {
  const num = Number(value)
  if (!Number.isFinite(num)) return String(value ?? '')
  if (num === 0) return '0'
  const abs = Math.abs(num)
  if (abs >= 1000 || abs < 0.01) return num.toExponential(1)
  if (abs >= 100) return num.toFixed(0)
  if (abs >= 10) return trimFixed(num, 1)
  return trimFixed(num, 2)
}

function formatMetric(value: unknown) {
  const num = Number(value)
  if (!Number.isFinite(num)) return 'Not available'
  if (Math.abs(num) >= 1000 || (Math.abs(num) > 0 && Math.abs(num) < 0.001)) {
    return num.toExponential(3)
  }
  return trimFixed(num, 3)
}

function trimFixed(value: number, digits: number) {
  return value.toFixed(digits).replace(/\.?0+$/, '')
}
