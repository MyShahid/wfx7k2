import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { fmtTime, toGW } from '../api'

const fmtValue = (gw) => (gw == null ? '–' : `${gw.toFixed(2)} GW`)

function ForecastTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  const noForecast = p.time.slice(14, 16) === '30' ? '– (forecasts are hourly)' : '– (none available)'
  return (
    <div style={{ background: 'var(--card)', border: '1px solid var(--border)', padding: '8px 10px', fontSize: 13 }}>
      <b>{fmtTime(label)} UTC</b>
      <div>Actual: {fmtValue(p.actual)}</div>
      <div>Forecast: {p.forecast == null ? noForecast : fmtValue(p.forecast)}</div>
      {p.published && <div>Published {fmtTime(p.published)} UTC, {p.lead} h ahead</div>}
    </div>
  )
}

export default function ForecastChart({ rows, description }) {
  // WINDFOR is hourly, so :30 rows have no forecast. To draw a continuous line
  // that still breaks where a forecast is genuinely missing, a :30 row is drawn
  // at the midpoint of its two neighbouring hourly forecasts when both exist.
  const data = rows.map((r, i) => {
    const prev = rows[i - 1]?.forecast
    const next = rows[i + 1]?.forecast
    const bridged = r.forecast == null && r.time.slice(14, 16) === '30' && prev != null && next != null
    return {
      time: r.time,
      actual: toGW(r.actual),
      forecast: toGW(r.forecast),
      forecastLine: bridged ? toGW((prev + next) / 2) : toGW(r.forecast),
      published: r.publishTime,
      lead: r.leadHours,
    }
  })
  return (
    <section className="card">
      <h2>Actual vs forecast wind generation</h2>
      <p className="muted">Forecast = {description} (GW)</p>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" />
          <XAxis dataKey="time" tickFormatter={fmtTime} minTickGap={60} stroke="var(--muted)" />
          <YAxis unit=" GW" stroke="var(--muted)" width={70} />
          <Tooltip content={<ForecastTooltip />} />
          <Legend />
          <Line type="monotone" dataKey="actual" name="Actual" stroke="var(--actual)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="forecastLine" name="Forecast" stroke="var(--forecast)" dot={false}
            strokeWidth={2} strokeDasharray="5 3" />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
