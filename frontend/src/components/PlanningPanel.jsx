import { fmtGW } from '../api'

// Turns the error statistics into a procurement rule of thumb.
export default function PlanningPanel({ m, horizon }) {
  if (!m || !m.count) return null
  const p10 = m.error_p10 // 10% of hours: actual was at least this far below/above forecast
  return (
    <section className="card planning">
      <h2>What this means for day-ahead buying</h2>
      <p>
        Using forecasts published <b>{horizon} h</b> ahead, actual wind was on average{' '}
        <b>{fmtGW(Math.abs(m.bias), 2)} {m.bias < 0 ? 'below' : 'above'}</b> the forecast.
      </p>
      <ul>
        <li>
          <b>Expected case:</b> plan wind at <b>forecast {m.error_p50 < 0 ? '−' : '+'} {fmtGW(Math.abs(m.error_p50))}</b>{' '}
          (median error).
        </li>
        <li>
          <b>Cautious case (90% cover):</b> plan wind at{' '}
          <b>forecast {p10 < 0 ? '−' : '+'} {fmtGW(Math.abs(p10))}</b>. In 9 out of 10 hours, actual wind
          was at least this much, so buying the rest from the day-ahead market covers the shortfall.
        </li>
      </ul>
      <p className="muted">
        Based on {m.count} hourly comparisons in the selected period. Past error is a guide, not a guarantee.
      </p>
    </section>
  )
}
