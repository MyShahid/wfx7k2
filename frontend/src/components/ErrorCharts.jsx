import { Bar, BarChart, CartesianGrid, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

const tooltipStyle = { background: 'var(--card)', border: '1px solid var(--border)' }

export function ErrorHistogram({ m }) {
  if (!m?.error_histogram) return null
  const data = m.error_histogram.map((b) => ({ ...b, label: `${b.from / 1000} to ${b.to / 1000}` }))
  return (
    <section className="card">
      <h2>How big are the errors?</h2>
      <p className="muted">Hours by error (actual − forecast, GW). Red = wind below forecast.</p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="label" stroke="var(--muted)" fontSize={11} />
          <YAxis stroke="var(--muted)" />
          <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v} hours`, 'Count']} />
          <Bar dataKey="count">
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
  return (
    <section className="card">
      <h2>Error by time of day</h2>
      <p className="muted">Average absolute error per hour (UTC, GW)</p>
      <ResponsiveContainer width="100%" height={260}>
        <BarChart data={data}>
          <CartesianGrid stroke="var(--grid)" vertical={false} />
          <XAxis dataKey="hour" stroke="var(--muted)" fontSize={11} interval={2} />
          <YAxis unit=" GW" stroke="var(--muted)" width={70} />
          <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${v.toFixed(2)} GW`, 'MAE']} />
          <Bar dataKey="mae" fill="var(--forecast)" />
        </BarChart>
      </ResponsiveContainer>
    </section>
  )
}
