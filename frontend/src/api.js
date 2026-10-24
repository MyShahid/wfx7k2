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

export const fetchSeries = (start, end, horizon) => get('series', { start, end, horizon })
export const fetchMetrics = (start, end, horizon) => get('metrics', { start, end, horizon })
export const fetchHorizonCurve = (start, end) => get('horizon-curve', { start, end })

// Helpers for display
export const toGW = (mw) => (mw == null ? null : mw / 1000)
export const fmtGW = (mw, digits = 1) => (mw == null ? '–' : `${(mw / 1000).toFixed(digits)} GW`)
export const fmtTime = (iso) => {
  const d = new Date(iso)
  const p = (n) => String(n).padStart(2, '0')
  return `${p(d.getUTCDate())} Jan ${p(d.getUTCHours())}:${p(d.getUTCMinutes())}`
}
