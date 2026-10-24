import { CartesianGrid, Legend, Line, LineChart, ReferenceArea, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

// `horizon`: the selected fixed horizon (fixed-horizon mode), else null.
// `leadRange`: { min, max } lead hours of the decision-time series, else null.
export default function HorizonChart({ curve, horizon, leadRange }) {
  if (!curve?.length) return null
  const data = curve.map((c) => ({ horizon: c.horizon, mae: c.mae / 1000, rmse: c.rmse / 1000, bias: c.bias / 1000 }))
  return (
    <section className="card">
      <h2>Does an earlier forecast mean a worse forecast?</h2>
      <p className="muted">Error vs how many hours ahead the forecast was made (GW)</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid stroke="var(--grid)" />
          {/* numeric axis so lines/bands can sit between the 2 h curve points */}
          <XAxis dataKey="horizon" type="number" domain={[0, 'dataMax']} allowDecimals={false} unit=" h" stroke="var(--muted)" />
          <YAxis unit=" GW" stroke="var(--muted)" width={70} />
          <Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }}
            formatter={(v, n) => [`${v.toFixed(2)} GW`, n]} labelFormatter={(h) => `${h} h ahead`} />
          <Legend />
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
