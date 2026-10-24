// Shared chart styling so tooltips, hover cursors and axes follow the theme
// tokens in index.css (light and dark).

export const tooltipProps = {
  contentStyle: {
    background: 'var(--card)', border: '1px solid var(--border)', borderRadius: 8,
    padding: '8px 10px', fontSize: 13, color: 'var(--text)',
  },
  labelStyle: { color: 'var(--text)', fontWeight: 600, marginBottom: 2 },
  itemStyle: { color: 'var(--text)', padding: 0 },
}

export const barCursor = { fill: 'var(--hover)' }
export const lineCursor = { stroke: 'var(--muted)', strokeWidth: 1, strokeDasharray: '3 3' }

export const axisProps = { stroke: 'var(--muted)', fontSize: 12, tickLine: false }

const STEPS = [0.1, 0.2, 0.25, 0.5, 1, 2, 2.5, 5, 10, 20, 25, 50, 100, 200, 250, 500, 1000]

// Evenly spaced round ticks covering [min, max], at most `maxTicks` of them.
export function roundTicks(min, max, maxTicks = 7) {
  for (const step of STEPS) {
    const lo = Math.floor(min / step) * step
    const hi = Math.max(Math.ceil(max / step) * step, lo + step)
    const n = Math.round((hi - lo) / step)
    if (n + 1 <= maxTicks) return Array.from({ length: n + 1 }, (_, i) => Number((lo + i * step).toFixed(2)))
  }
  return [min, max]
}

// "0", "0.5 GW", "1.0 GW" when the ticks need a decimal, otherwise "5 GW"
export function gwTick(ticks) {
  const decimals = ticks.some((t) => !Number.isInteger(t)) ? 1 : 0
  return (v) => (v === 0 ? '0' : `${v.toFixed(decimals)} GW`)
}

const MONTHS = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
export const fmtDay = (iso) => {
  const d = new Date(iso)
  return `${d.getUTCDate()} ${MONTHS[d.getUTCMonth()]}`
}
