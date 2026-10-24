import { useEffect, useState } from 'react'
import './App.css'
import { describeSelection, fetchHorizonCurve, fetchMeta, fetchMetrics, fetchSeries } from './api'
import Controls from './components/Controls'
import KpiCards from './components/KpiCards'
import BiasNote from './components/BiasNote'
import PlanningPanel from './components/PlanningPanel'
import ForecastChart from './components/ForecastChart'
import { ErrorByHour, ErrorHistogram } from './components/ErrorCharts'
import HorizonChart from './components/HorizonChart'

const FALLBACK_GATE_CLOSURE = '09:20'

export default function App() {
  const [filters, setFilters] = useState({
    start: '2026-01-01', end: '2026-01-31',
    mode: 'decision', gateClosure: FALLBACK_GATE_CLOSURE, horizon: 24,
  })
  const [rows, setRows] = useState([])
  const [metrics, setMetrics] = useState(null)
  const [curve, setCurve] = useState([])
  const [curveError, setCurveError] = useState('')
  const [error, setError] = useState('')
  // Loading = the filters have changed since the last request settled
  const [settledKey, setSettledKey] = useState(null)

  const update = (patch) => setFilters((f) => ({ ...f, ...patch }))
  const { start, end, mode, gateClosure, horizon } = filters
  const description = describeSelection(filters)
  const requestKey = [start, end, mode, gateClosure, horizon].join('|')
  const loading = settledKey !== requestKey

  // Lead-time range of the decision-time series, shown on the horizon chart
  const leads = mode === 'decision' ? rows.map((r) => r.leadHours).filter((h) => h != null) : []
  const leadRange = leads.length ? { min: Math.min(...leads), max: Math.max(...leads) } : null

  // Default gate closure comes from the API; keep the fallback if that fails
  // or if the user has already changed it
  useEffect(() => {
    fetchMeta()
      .then((m) => m.default_gate_closure && setFilters((f) => (
        f.gateClosure === FALLBACK_GATE_CLOSURE ? { ...f, gateClosure: m.default_gate_closure } : f)))
      .catch(() => {})
  }, [])

  // Series + metrics depend on all filters
  useEffect(() => {
    let cancelled = false
    const selection = mode === 'decision' ? { gate_closure: gateClosure } : { horizon }
    Promise.all([fetchSeries(start, end, selection), fetchMetrics(start, end, selection)])
      .then(([s, m]) => { if (!cancelled) { setRows(s); setMetrics(m); setError('') } })
      .catch((e) => { if (!cancelled) setError(e.message) })
      .finally(() => { if (!cancelled) setSettledKey(requestKey) })
    return () => { cancelled = true }
  }, [start, end, mode, gateClosure, horizon, requestKey])

  // Horizon curve depends only on the date range
  useEffect(() => {
    let cancelled = false
    fetchHorizonCurve(start, end)
      .then((c) => { if (!cancelled) { setCurve(c); setCurveError('') } })
      .catch((e) => { if (!cancelled) { setCurve([]); setCurveError(e.message) } })
    return () => { cancelled = true }
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

      <Controls start={start} end={end} mode={mode} gateClosure={gateClosure} horizon={horizon}
        onChange={update} />

      {error && <div className="error">Could not load data: {error}</div>}
      {loading && <div className="loading">Loading…</div>}

      <KpiCards m={metrics} />
      <BiasNote m={metrics} curve={curve} />
      <ForecastChart rows={rows} description={description} />
      <PlanningPanel m={metrics} description={description} />
      <div className="grid-2">
        <ErrorHistogram m={metrics} />
        <ErrorByHour m={metrics} />
      </div>
      {curveError && <div className="error">Could not load the horizon curve: {curveError}</div>}
      <HorizonChart curve={curve} horizon={mode === 'horizon' ? horizon : null} leadRange={leadRange} />

      <footer className="muted">
        Data: Elexon BMRS FUELHH (actual, fuel type WIND) and WINDFOR (forecast). Times in UTC. 1 GW = 1,000 MW.
      </footer>
    </div>
  )
}
