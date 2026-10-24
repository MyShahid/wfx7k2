// Small wrapper around the backend API.
const BASE = import.meta.env.VITE_API_BASE || ''

async function get(path, params) {
  const qs = new URLSearchParams(params).toString()
  const res = await fetch(`${BASE}/api/${path}?${qs}`)
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `Request failed (${res.status})`)
  }
  return res.json()
}

// `selection` is either { horizon } or { gate_closure }
export const fetchSeries = (start, end, selection) => get('series', { start, end, ...selection })
export const fetchMetrics = (start, end, selection) => get('metrics', { start, end, ...selection })
export const fetchHorizonCurve = (start, end) => get('horizon-curve', { start, end })
export const fetchMeta = () => get('meta', {})

// How the forecast was picked, in words, for the active mode
export const describeSelection = ({ mode, gateClosure, horizon }) =>
  mode === 'decision'
    ? `latest forecast available at ${gateClosure} the day before`
    : `latest forecast published at least ${horizon} h before each hour`

// Helpers for display
export const toGW = (mw) => (mw == null ? null : mw / 1000)
export const fmtGW = (mw, digits = 1) => (mw == null ? '–' : `${(mw / 1000).toFixed(digits)} GW`)
export const fmtTime = (iso) => {
  const d = new Date(iso)
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getUTCDate())} Jan ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`
}
