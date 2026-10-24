import { CartesianGrid, Legend, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'
import { axisProps, gwTick, lineCursor, roundTicks, tooltipProps } from './chartStyles'

// `horizon`: the selected fixed horizon (fixed-horizon mode), else null.
// `leadRange`: { min, max } lead hours of the decision-time series, else null.
export default function HorizonChart({ curve, horizon, leadRange }) {
  if (!curve?.length) return null
  const data = curve.map((c) => ({ horizon: c.horizon, mae: c.mae / 1000, rmse: c.rmse / 1000, bias: c.bias / 1000 }))
  // Pad 0.5 GW around all three lines (and 0) so none sits on the plot edge
  const values = data.flatMap((d) => [d.mae, d.rmse, d.bias])
  const yTicks = roundTicks(Math.min(0, ...values) - 0.5, Math.max(0, ...values) + 0.5, 9)
  const xTicks = roundTicks(0, Math.max(...data.map((d) => d.horizon)), 9)
  return (
    <section className="card">
      <h2>Does an earlier forecast mean a worse forecast?</h2>
      <p className="muted">Error vs how many hours ahead the forecast was made (GW)</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data} margin={{ top: 8, right: 16, bottom: 0, left: 0 }}>
          <CartesianGrid stroke="var(--grid)" />
          {/* numeric axis so lines/bands can sit between the 2 h curve points */}
          <XAxis dataKey="horizon" type="number" {...axisProps} ticks={xTicks} domain={[0, xTicks.at(-1)]} unit=" h" />
          <YAxis {...axisProps} ticks={yTicks} domain={[yTicks[0], yTicks.at(-1)]} tickFormatter={gwTick(yTicks)} width={56} />
          <Tooltip {...tooltipProps} cursor={lineCursor}
            formatter={(v, n) => [`${v.toFixed(2)} GW`, n]} labelFormatter={(h) => `${h} h ahead`} />
          <Legend />
          <ReferenceLine y={0} stroke="var(--muted)" strokeOpacity={0.7} />
          {leadRange && (
            <ReferenceArea x1={leadRange.min} x2={leadRange.max} ifOverflow="hidden" fill="var(--forecast)" fillOpacity={0.12}
              label={{ value: 'decision-time lead', position: 'insideTop', fill: 'var(--muted)', fontSize: 11 }} />
          )}
          {horizon != null && (
            <ReferenceLine x={horizon} stroke="var(--muted)" strokeDasharray="4 4" label={{ value: 'selected', fill: 'var(--muted)', fontSize: 11 }} />
          )}
          <Line dataKey="mae" name="MAE" stroke="var(--forecast)" dot={false} strokeWidth={2} />
          <Line dataKey="rmse" name="RMSE" stroke="var(--actual)" dot={false} strokeWidth={2} />
          <Line dataKey="bias" name="Bias" stroke="var(--bad)" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
