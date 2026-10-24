import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { fmtTime, toGW } from '../api'

export default function ForecastChart({ rows, description }) {
  const data = rows.map((r) => ({
    time: r.time,
    actual: toGW(r.actual),
    forecast: toGW(r.forecast),
    published: r.publishTime,
  }))
  return (
    <section className="card">
      <h2>Actual vs forecast wind generation</h2>
      <p className="muted">Forecast = {description} (GW)</p>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" />
          <XAxis dataKey="time" tickFormatter={fmtTime} minTickGap={60} stroke="var(--muted)" />
          <YAxis unit=" GW" stroke="var(--muted)" width={70} />
          <Tooltip
            labelFormatter={fmtTime}
            formatter={(v, name) => [v == null ? '–' : `${v.toFixed(2)} GW`, name]}
            contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }}
          />
          <Legend />
          <Line type="monotone" dataKey="actual" name="Actual" stroke="var(--actual)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="forecast" name="Forecast" stroke="var(--forecast)" dot={false}
            strokeWidth={2} strokeDasharray="5 3" connectNulls />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
