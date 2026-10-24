import { fmtGW } from '../api'

// Turns the error statistics into a procurement rule of thumb.
export default function PlanningPanel({ m, description }) {
  if (!m || !m.count) return null
  const p10 = m.error_p10 // 10% of hours: actual was at least this far below/above forecast
  return (
    <section className="card planning">
      <h2>What this means for day-ahead buying</h2>
      <p>
        Using the <b>{description}</b>, actual wind was on average{' '}
        <b>{fmtGW(Math.abs(m.bias), 2)} {m.bias < 0 ? 'below' : 'above'}</b> the forecast.
      </p>
      <ul>
        <li>
          <b>Expected case:</b> plan wind at <b>forecast {m.error_p50 < 0 ? '−' : '+'} {fmtGW(Math.abs(m.error_p50))}</b>{' '}
          (median error).
        </li>
        <li>
          <b>Cautious case (90% cover):</b> plan wind at{' '}
          <b>forecast {p10 < 0 ? '−' : '+'} {fmtGW(Math.abs(p10))}</b>. This is the wind level that was met or
          exceeded in 9 out of 10 hours. Buying day-ahead to cover demand minus this cautious wind leaves roughly
          a 1-in-10 chance per hour of a shortfall, which would be covered intraday or through imbalance.
        </li>
      </ul>
      <p>The adjustment is applied to each hour's forecast and floored at 0 MW (wind cannot be negative).</p>
      <p className="muted">
        Based on {m.count} hourly comparisons in the selected period. Past error is a guide, not a guarantee.
      </p>
    </section>
  )
}
