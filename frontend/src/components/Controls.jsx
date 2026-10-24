export default function Controls({ start, end, horizon, onChange }) {
  return (
    <section className="controls">
      <label>
        From
        <input id="start" type="date" min="2026-01-01" max="2026-01-31" value={start}
          onChange={(e) => onChange({ start: e.target.value })} />
      </label>
      <label>
        To
        <input id="end" type="date" min="2026-01-01" max="2026-01-31" value={end}
          onChange={(e) => onChange({ end: e.target.value })} />
      </label>
      <label className="horizon">
        Forecast horizon: <strong>{horizon} h</strong>
        <input id="horizon" type="range" min="0" max="40" step="1" value={horizon}
          onChange={(e) => onChange({ horizon: Number(e.target.value) })} />
        <small>Uses the latest forecast published at least {horizon} h before each hour</small>
      </label>
      <div className="presets">
        <span>Quick pick:</span>
        <button onClick={() => onChange({ horizon: 4 })}>4 h (intraday)</button>
        <button onClick={() => onChange({ horizon: 24 })}>24 h (day-ahead)</button>
        <button onClick={() => onChange({ horizon: 36 })}>36 h</button>
      </div>
    </section>
  )
}
