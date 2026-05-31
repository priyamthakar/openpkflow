import { useState } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer, ReferenceLine,
} from 'recharts'

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
}

export function PKChart({
  series,
  xLabel = 'Time (h)',
  yLabel = 'Concentration',
  doseTimes,
  thresholdY,
  thresholdLabel = '85% dissolved',
  lambdaZ,
}: Props) {
  const [logScale, setLogScale] = useState(false)

  // Merge all series into a shared time grid
  const allTimes = [...new Set(series.flatMap((s) => s.times))].sort((a, b) => a - b)
  const data = allTimes.map((t) => {
    const row: Record<string, number | null> = { time: t }
    series.forEach((s) => {
      const idx = s.times.indexOf(t)
      row[s.name] = idx !== -1 ? (logScale && s.concs[idx] <= 0 ? null : s.concs[idx]) : null
    })
    return row
  })

  const COLORS = ['#5e6ad2', '#3dd68c', '#f0a731', '#e5534b', '#a78bfa']

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'flex-end', marginBottom: 8 }}>
        <button
          onClick={() => setLogScale((l) => !l)}
          style={{
            fontSize: 11,
            padding: '4px 10px',
            borderRadius: 5,
            border: '1px solid var(--border-2)',
            background: logScale ? 'var(--accent-muted)' : 'var(--surface-2)',
            color: logScale ? 'var(--accent)' : 'var(--text-muted)',
            cursor: 'pointer',
          }}
        >
          {logScale ? 'Linear' : 'Semi-log'}
        </button>
      </div>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 4, right: 20, bottom: 4, left: 0 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
          <XAxis
            dataKey="time"
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            label={{ value: xLabel, position: 'insideBottom', offset: -4, fill: 'var(--text-muted)', fontSize: 11 }}
          />
          <YAxis
            scale={logScale ? 'log' : 'auto'}
            domain={logScale ? ['auto', 'auto'] : [0, 'auto']}
            tick={{ fill: 'var(--text-muted)', fontSize: 11 }}
            label={{ value: yLabel, angle: -90, position: 'insideLeft', fill: 'var(--text-muted)', fontSize: 11 }}
          />
          <Tooltip
            contentStyle={{ background: 'var(--surface-2)', border: '1px solid var(--border)', borderRadius: 6, fontSize: 12 }}
            labelStyle={{ color: 'var(--text-muted)' }}
            itemStyle={{ color: 'var(--text)' }}
          />
          {series.length > 1 && <Legend wrapperStyle={{ fontSize: 12, color: 'var(--text-muted)' }} />}

          {/* Dose markers */}
          {doseTimes?.map((dt) => (
            <ReferenceLine key={dt} x={dt} stroke="var(--danger)" strokeDasharray="4 3" strokeOpacity={0.6} />
          ))}

          {/* 85% threshold line */}
          {thresholdY != null && (
            <ReferenceLine y={thresholdY} stroke="var(--warning)" strokeDasharray="4 3"
              label={{ value: thresholdLabel, fill: 'var(--warning)', fontSize: 10 }} />
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
            />
          ))}

          {/* Lambda-z selected points */}
          {lambdaZ && lambdaZ.times.map((t, i) => (
            <ReferenceLine key={i} x={t} stroke="var(--accent)" strokeOpacity={0.5} strokeDasharray="2 2" />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}
