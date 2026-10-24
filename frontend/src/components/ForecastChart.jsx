import { CartesianGrid, Legend, Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { fmtTime, toGW } from '../api'
import { axisProps, fmtDay, gwTick, lineCursor, roundTicks, tooltipProps } from './chartStyles'

const fmtValue = (gw) => (gw == null ? '–' : `${gw.toFixed(2)} GW`)

function ForecastTooltip({ active, payload, label }) {
  if (!active || !payload?.length) return null
  const p = payload[0].payload
  const noForecast = p.time.slice(14, 16) === '30' ? '– (forecasts are hourly)' : '– (none available)'
  return (
    <div style={tooltipProps.contentStyle}>
      <div style={tooltipProps.labelStyle}>{fmtTime(label)} UTC</div>
      <div>Actual: {fmtValue(p.actual)}</div>
      <div>Forecast: {p.forecast == null ? noForecast : fmtValue(p.forecast)}</div>
      {p.published && <div>Published {fmtTime(p.published)} UTC, {p.lead} h ahead</div>}
    </div>
  )
}

// Midnight ticks: every day for short ranges, otherwise calendar-aligned
// (1, 5, 10 … Jan), keeping the first day unless an aligned tick is next to it.
function dayTicks(data) {
  const days = data.filter((d) => d.time.endsWith('T00:00:00Z')).map((d) => d.time)
  const every = days.length <= 7 ? 1 : days.length <= 14 ? 2 : 5
  if (every === 1) return days
  const aligned = days.filter((t) => Number(t.slice(8, 10)) % every === 0)
  const keepFirst = !aligned.length || days.indexOf(aligned[0]) >= 2
  return keepFirst && aligned[0] !== days[0] ? [days[0], ...aligned] : aligned
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
  const yMax = Math.max(0, ...data.flatMap((d) => [d.actual ?? 0, d.forecastLine ?? 0]))
  const yTicks = roundTicks(0, yMax)
  return (
    <section className="card">
      <h2>Actual vs forecast wind generation</h2>
      <p className="muted">Forecast = {description} (GW)</p>
      <ResponsiveContainer width="100%" height={340}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 8, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" />
          <XAxis dataKey="time" {...axisProps} ticks={dayTicks(data)} interval={0} tickFormatter={fmtDay} />
          <YAxis {...axisProps} ticks={yTicks} domain={[0, yTicks.at(-1)]} tickFormatter={gwTick(yTicks)} width={56} />
          <Tooltip content={<ForecastTooltip />} cursor={lineCursor} />
          <Legend />
          <Line type="monotone" dataKey="actual" name="Actual" stroke="var(--actual)" dot={false} strokeWidth={2} />
          <Line type="monotone" dataKey="forecastLine" name="Forecast" stroke="var(--forecast)" dot={false}
            strokeWidth={2} strokeDasharray="5 3" />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
