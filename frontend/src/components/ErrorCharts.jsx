import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { axisProps, barCursor, gwTick, roundTicks, tooltipProps } from './chartStyles'

export function ErrorHistogram({ m }) {
  if (!m?.error_histogram) return null
  const data = m.error_histogram.map((b) => ({ ...b, label: `${b.from / 1000} to ${b.to / 1000}` }))
  const ticks = roundTicks(0, Math.max(...data.map((d) => d.count)))
  return (
    <section className="card">
      <h2>How big are the errors?</h2>
      <p className="muted">Hours by error (actual − forecast, GW). Red = wind below forecast.</p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="label" {...axisProps} fontSize={11} />
          <YAxis {...axisProps} ticks={ticks} domain={[0, ticks.at(-1)]} width={44} />
          <Tooltip {...tooltipProps} cursor={barCursor} formatter={(v) => [`${v} hours`, 'Count']} />
          <Bar dataKey="count" radius={[3, 3, 0, 0]}>
            {data.map((d) => (
              <Cell key={d.from} fill={d.from < 0 ? 'var(--bad)' : 'var(--good)'} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </section>
  )
}

export function ErrorByHour({ m }) {
  if (!m?.mae_by_hour) return null
  const data = m.mae_by_hour.map((h) => ({ hour: `${h.hour}:00`, mae: h.mae / 1000 }))
  const ticks = roundTicks(0, Math.max(...data.map((d) => d.mae)))
  return (
    <section className="card">
      <h2>Error by time of day</h2>
      <p className="muted">Average absolute error per hour (UTC, GW)</p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="hour" {...axisProps} fontSize={11} interval={2} />
          <YAxis {...axisProps} ticks={ticks} domain={[0, ticks.at(-1)]} tickFormatter={gwTick(ticks)} width={64} />
          <Tooltip {...tooltipProps} cursor={barCursor} formatter={(v) => [`${v.toFixed(2)} GW`, 'MAE']} />
          <Bar dataKey="mae" fill="var(--forecast)" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </section>
  )
}
