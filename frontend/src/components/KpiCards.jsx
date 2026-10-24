import { fmtGW } from '../api'

export default function KpiCards({ m }) {
  if (!m || !m.count) return null
  const cards = [
    { label: 'Average wind output', value: fmtGW(m.actual_mean), note: 'Actual, selected period' },
    { label: 'Typical error (MAE)', value: fmtGW(m.mae, 2), note: `${m.nmae_pct}% of average output` },
    { label: 'Bias', value: fmtGW(m.bias, 2),
      note: m.bias < 0 ? 'Forecast is too high on average' : 'Forecast is too low on average',
      tone: Math.abs(m.bias) > 500 ? 'warn' : '' },
    { label: 'RMSE', value: fmtGW(m.rmse, 2), note: 'Penalises large misses' },
    { label: '90% of hours within', value: `± ${fmtGW(m.abs_error_p90)}`, note: 'Absolute error, P90' },
    { label: 'Worst shortfall', value: fmtGW(m.max_shortfall), note: 'Wind far below forecast', tone: 'bad' },
  ]
  return (
    <section className="kpis">
      {cards.map((c) => (
        <div key={c.label} className={`kpi ${c.tone || ''}`}>
          <span className="kpi-label">{c.label}</span>
          <b>{c.value}</b>
          <small>{c.note}</small>
        </div>
      ))}
    </section>
  )
}
