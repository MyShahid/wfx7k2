const QUICK_PICKS = [
  { hours: 4, label: '4 h (intraday)' },
  { hours: 24, label: '24 h (day-ahead)' },
  { hours: 36, label: '36 h' },
]

// Three groups on one row (period | mode | mode settings); each group is a
// label line followed by a control line, so the controls share a baseline.
export default function Controls({ start, end, mode, gateClosure, horizon, onChange }) {
  return (
    <section className="controls">
      <div className="control-group">
        <span className="control-label">Period</span>
        <div className="control-row">
          <label className="field">
            From
            <input id="start" type="date" min="2026-01-01" max="2026-01-31" value={start}
              onChange={(e) => onChange({ start: e.target.value })} />
          </label>
          <label className="field">
            To
            <input id="end" type="date" min="2026-01-01" max="2026-01-31" value={end}
              onChange={(e) => onChange({ end: e.target.value })} />
          </label>
        </div>
      </div>

      <div className="control-group">
        <span className="control-label" id="mode-label">Forecast</span>
        <div className="control-row">
          <div className="segmented" role="group" aria-labelledby="mode-label">
            <button aria-pressed={mode === 'decision'} onClick={() => onChange({ mode: 'decision' })}>Decision time</button>
            <button aria-pressed={mode === 'horizon'} onClick={() => onChange({ mode: 'horizon' })}>Fixed horizon</button>
          </div>
        </div>
      </div>

      {mode === 'decision' ? (
        <div className="control-group">
          <label className="control-label" htmlFor="gate-closure">Gate closure</label>
          <div className="control-row">
            <input id="gate-closure" type="time" value={gateClosure}
              onChange={(e) => e.target.value && onChange({ gateClosure: e.target.value })} />
          </div>
          <small>Uses the latest forecast published before this time on the day before delivery (UK time)</small>
        </div>
      ) : (
        <div className="control-group grow">
          <label className="control-label" htmlFor="horizon">Forecast horizon: <strong>{horizon} h</strong></label>
          <div className="control-row">
            <input id="horizon" type="range" min="0" max="40" step="1" value={horizon}
              onChange={(e) => onChange({ horizon: Number(e.target.value) })} />
            <div className="chips" role="group" aria-label="Quick pick">
              {QUICK_PICKS.map((q) => (
                <button key={q.hours} aria-pressed={horizon === q.hours} onClick={() => onChange({ horizon: q.hours })}>
                  {q.label}
                </button>
              ))}
            </div>
          </div>
          <small>Uses the latest forecast published at least {horizon} h before each hour</small>
        </div>
      )}
    </section>
  )
}
