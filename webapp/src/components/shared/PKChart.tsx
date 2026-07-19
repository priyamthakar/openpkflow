import { useCallback, useRef, useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'
import { Download, LayoutGrid, Rows3 } from 'lucide-react'
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

const SERIES_VARS = [
  'var(--chart-1)',
  'var(--chart-2)',
  'var(--chart-3)',
  'var(--chart-4)',
  'var(--chart-5)',
]

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
  const [showDots, setShowDots] = useState(false)
  const [smallMultiples, setSmallMultiples] = useState(false)
  const [hiddenSeries, setHiddenSeries] = useState<Set<string>>(new Set())
  const rootRef = useRef<HTMLDivElement>(null)

  const toggleSeries = useCallback((key: string) => {
    setHiddenSeries((prev) => {
      const next = new Set(prev)
      if (next.has(key)) next.delete(key)
      else next.add(key)
      return next
    })
  }, [])

  const exportPng = useCallback(() => {
    // Legend swatches are also .recharts-surface and precede the plot in DOM order,
    // so scope to the direct child of the chart wrapper.
    const svg = rootRef.current?.querySelector('.recharts-wrapper > svg.recharts-surface')
    if (!svg) return
    const clone = svg.cloneNode(true) as SVGElement
    const bounds = svg.getBoundingClientRect()
    clone.setAttribute('xmlns', 'http://www.w3.org/2000/svg')
    clone.setAttribute('width', String(bounds.width))
    clone.setAttribute('height', String(bounds.height))
    const styles = getComputedStyle(document.documentElement)
    // The serialized SVG is rendered as a standalone document with no :root, so any
    // var(--token) left in an attribute would resolve to nothing. Inline them first.
    const resolveVars = (value: string) =>
      value.replace(/var\((--[\w-]+)\)/g, (whole, token: string) => {
        return styles.getPropertyValue(token).trim() || whole
      })
    for (const el of [clone, ...Array.from(clone.querySelectorAll('*'))]) {
      for (const attr of ['stroke', 'fill', 'color', 'style']) {
        const value = el.getAttribute(attr)
        if (value?.includes('var(')) el.setAttribute(attr, resolveVars(value))
      }
    }
    clone.setAttribute('font-family', getComputedStyle(svg).fontFamily || 'sans-serif')
    const bg = styles.getPropertyValue('--surface').trim() || '#ffffff'
    const rect = document.createElementNS('http://www.w3.org/2000/svg', 'rect')
    rect.setAttribute('width', '100%')
    rect.setAttribute('height', '100%')
    rect.setAttribute('fill', bg)
    clone.insertBefore(rect, clone.firstChild)
    const url = URL.createObjectURL(new Blob([clone.outerHTML], { type: 'image/svg+xml' }))
    const img = new Image()
    img.onload = () => {
      const canvas = document.createElement('canvas')
      const scale = 2
      canvas.width = bounds.width * scale
      canvas.height = bounds.height * scale
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      ctx.scale(scale, scale)
      ctx.drawImage(img, 0, 0)
      URL.revokeObjectURL(url)
      const a = document.createElement('a')
      a.href = canvas.toDataURL('image/png')
      a.download = 'pk_chart.png'
      a.click()
    }
    img.src = url
  }, [])

  const visibleSeries = series.filter((s) => !hiddenSeries.has(s.name))

  const chartFor = (subset: Series[], height: number, showLegend: boolean) => {
    // Render every series in `subset` so Recharts keeps a legend entry for hidden ones
    // (they are greyed via `hide`); derive the axis domain from the visible ones only.
    const shown = subset.filter((s) => !hiddenSeries.has(s.name))
    const domainSeries = shown.length > 0 ? shown : subset
    const allTimes = [...new Set(domainSeries.flatMap((s) => s.times))].sort((a, b) => a - b)
    const logSafeTimes = logScale
      ? allTimes.filter((t) =>
          domainSeries.every((s) => {
            const idx = s.times.indexOf(t)
            return idx === -1 || s.concs[idx] > 0
          }),
        )
      : allTimes
    const data = logSafeTimes.map((t) => {
      const row: Record<string, number | null> = { time: t }
      subset.forEach((s) => {
        const idx = s.times.indexOf(t)
        const val = idx !== -1 ? s.concs[idx] : null
        row[s.name] = logScale && val != null && val <= 0 ? null : val
      })
      return row
    })
    return (
      <ResponsiveContainer width="100%" height={height}>
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
          {showLegend && subset.length > 1 && (
            <Legend
              wrapperStyle={{ fontSize: 14, color: 'var(--text-muted)', cursor: 'pointer' }}
              onClick={(e) => {
                if (e.dataKey) toggleSeries(String(e.dataKey))
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
          {subset.map((s) => {
            const colorIdx = series.indexOf(s)
            return (
              <Line
                key={s.name}
                type="monotone"
                dataKey={s.name}
                stroke={s.color ?? SERIES_VARS[colorIdx % SERIES_VARS.length]}
                strokeWidth={2}
                dot={
                  showDots
                    ? { r: 3, strokeWidth: 1, fill: 'var(--surface)' }
                    : false
                }
                activeDot={showDots ? { r: 4 } : undefined}
                strokeDasharray={s.dashed ? '6 3' : undefined}
                connectNulls={false}
                hide={hiddenSeries.has(s.name)}
                isAnimationActive={true}
                animationDuration={600}
              />
            )
          })}
          {lambdaZ?.times.map((t, i) => (
            <ReferenceLine key={`lz-${i}`} x={t} stroke="var(--accent)" strokeOpacity={0.5} strokeDasharray="2 2" />
          ))}
        </LineChart>
      </ResponsiveContainer>
    )
  }

  return (
    <div ref={rootRef} className={cn('relative', className)}>
      <div className="flex justify-end mb-2 gap-1">
        <ToolbarButton
          active={showDots}
          onClick={() => setShowDots((d) => !d)}
          title="Toggle point markers"
        >
          Points
        </ToolbarButton>
        {series.length > 1 && (
          <ToolbarButton
            active={smallMultiples}
            onClick={() => setSmallMultiples((m) => !m)}
            title="Split each series into its own panel"
          >
            {smallMultiples ? <Rows3 size={13} /> : <LayoutGrid size={13} />}
            Panels
          </ToolbarButton>
        )}
        <ToolbarButton active={logScale} onClick={() => setLogScale((l) => !l)}>
          {logScale ? 'Linear' : 'Semi-log'}
        </ToolbarButton>
        <ToolbarButton onClick={exportPng} title="Download chart as PNG">
          <Download size={13} />
          PNG
        </ToolbarButton>
      </div>

      {logScale && (
        <p className="text-[11px] text-text-dim mb-1.5">
          Non-positive values are hidden on log scale.
        </p>
      )}

      {smallMultiples && series.length > 1 ? (
        <div className="grid gap-3 sm:grid-cols-2">
          {visibleSeries.map((s) => (
            <div key={s.name} className="min-w-0">
              <p className="font-mono-ui text-[11px] uppercase tracking-[0.1em] text-text-muted mb-1 truncate">
                {s.name}
              </p>
              {chartFor([s], 200, false)}
            </div>
          ))}
        </div>
      ) : (
        chartFor(series, 320, true)
      )}
    </div>
  )
}

function ToolbarButton({
  active,
  onClick,
  title,
  children,
}: {
  active?: boolean
  onClick: () => void
  title?: string
  children: React.ReactNode
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      title={title}
      className={cn(
        'inline-flex items-center justify-center gap-1 rounded-sm text-xs font-medium border transition-colors',
        // comfortable tap target on touch layouts, original density from sm up
        'min-h-9 px-3 py-2 sm:min-h-0 sm:px-2.5 sm:py-1',
        active
          ? 'bg-accent-muted border-accent/30 text-accent'
          : 'bg-surface-2 border-border-2 text-text-muted hover:text-text hover:border-border',
      )}
    >
      {children}
    </button>
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
