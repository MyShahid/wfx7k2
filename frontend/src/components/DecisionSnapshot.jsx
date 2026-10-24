// What a day-ahead buyer had at gate closure for the selected period, built
// from the decision-time series rows (one hourly forecast per delivery hour).

const ukDate = (iso) => new Date(iso).toLocaleDateString('en-CA', { timeZone: 'Europe/London' })
const daysBetween = (a, b) => Math.round((Date.parse(a) - Date.parse(b)) / 86_400_000)
const fmtGWh = (mwh) => `${Math.round(mwh / 1000).toLocaleString('en-GB')} GWh`
const dayText = (n) => (n === 1 ? 'the day before' : n === 0 ? 'the delivery day' : `${n} days before`)

export default function DecisionSnapshot({ rows, gateClosure }) {
  const used = rows.filter((r) => r.forecast != null)
  if (!used.length) return null

  // Group hours by the run they used: publish time of day (UTC) and days before delivery
  const runs = new Map()
  for (const r of used) {
    const key = `${r.publishTime.slice(11, 16)} UTC on ${dayText(daysBetween(ukDate(r.time), ukDate(r.publishTime)))}`
    runs.set(key, (runs.get(key) ?? 0) + 1)
  }
  const runList = [...runs.entries()].sort((a, b) => b[1] - a[1])

  const leads = used.map((r) => r.leadHours)
  const meanLead = leads.reduce((s, h) => s + h, 0) / leads.length
  // Hourly MW values, one hour each, so the sums are MWh
  const forecastMWh = used.reduce((s, r) => s + r.forecast, 0)
  const actualMWh = used.reduce((s, r) => s + r.actual, 0)
  const diffPct = (100 * (actualMWh - forecastMWh)) / forecastMWh

  const figures = [
    runList.length === 1
      ? { label: 'Forecast run used', value: runList[0][0].split(' on ')[0], note: `Published on ${runList[0][0].split(' on ')[1]}` }
      : { label: 'Forecast runs used', value: `${runList.length} runs`,
          note: runList.slice(0, 2).map(([k, n]) => `${k} (${n} h)`).join('; ') },
    { label: 'Lead time', value: `${Math.min(...leads)}–${Math.max(...leads)} h`,
      note: `Before delivery, mean ${meanLead.toFixed(1)} h` },
    { label: 'Forecast energy', value: fmtGWh(forecastMWh), note: `${used.length} hours with a forecast` },
    { label: 'Actual energy', value: fmtGWh(actualMWh),
      note: `${diffPct >= 0 ? '+' : '−'}${Math.abs(diffPct).toFixed(1)}% vs forecast, same hours` },
  ]

  return (
    <section className="card">
      <h2>Decision snapshot</h2>
      <p className="muted">What you would have had at {gateClosure} UK time on the day before delivery</p>
      <div className="figures">
        {figures.map((f) => (
          <div key={f.label} className="figure">
            <span className="figure-label">{f.label}</span>
            <b>{f.value}</b>
            <small>{f.note}</small>
          </div>
        ))}
      </div>
    </section>
  )
}
