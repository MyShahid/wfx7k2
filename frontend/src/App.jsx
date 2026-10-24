import { useEffect, useState } from 'react'
import './App.css'
import { fetchHorizonCurve, fetchMetrics, fetchSeries } from './api'
import Controls from './components/Controls'
import KpiCards from './components/KpiCards'
import PlanningPanel from './components/PlanningPanel'
import ForecastChart from './components/ForecastChart'
import { ErrorByHour, ErrorHistogram } from './components/ErrorCharts'
import HorizonChart from './components/HorizonChart'

export default function App() {
  const [filters, setFilters] = useState({ start: '2026-01-01', end: '2026-01-31', horizon: 24 })
  const [rows, setRows] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [curve, setCurve] = useState([])
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(true)

  const update = (patch) => setFilters((f) => ({ ...f, ...patch }))
  const { start, end, horizon } = filters

  // Series + metrics depend on all filters
  useEffect(() => {
    let cancelled = false
    setLoading(true)
    Promise.all([fetchSeries(start, end, horizon), fetchMetrics(start, end, horizon)])
      .then(([s, m]) => { if (!cancelled) { setRows(s); setMetrics(m); setError('') } })
      .catch((e) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setLoading(false) })
    return () => { cancelled = true }
  }, [start, end, horizon])

  // Horizon curve depends only on the date range
  useEffect(() => {
    fetchHorizonCurve(start, end).then(setCurve).catch(() => setCurve([]))
  }, [start, end])

  return (
    <div className="app">
      <header>
        <div>
          <p className="eyebrow">GB national wind · Elexon BMRS · January 2026</p>
          <h1>Wind Forecast Monitor</h1>
          <p className="muted">
            See the wind forecast you would have had at decision time, and how far off it turned out to be.
          </p>
        </div>
      </header>

      <Controls start={start} end={end} horizon={horizon} onChange={update} />

      {error && <div className="error">Could not load data: {error}</div>}
      {loading && <div className="loading">Loading…</div>}

      <KpiCards m={metrics} />
      <ForecastChart rows={rows} horizon={horizon} />
      <PlanningPanel m={metrics} horizon={horizon} />
      <div className="grid-2">
        <ErrorHistogram m={metrics} />
        <ErrorByHour m={metrics} />
      </div>
      <HorizonChart curve={curve} horizon={horizon} />

      <footer className="muted">
        Data: Elexon BMRS FUELHH (actual, fuel type WIND) and WINDFOR (forecast). Times in UTC. 1 GW = 1,000 MW.
      </footer>
    </div>
  )
}
