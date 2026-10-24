import { CartesianGrid, Legend, Line, LineChart, ReferenceLine, ResponsiveContainer, Tooltip, XAxis, YAxis } from 'recharts'

export default function HorizonChart({ curve, horizon }) {
  if (!curve?.length) return null
  const data = curve.map((c) => ({ horizon: c.horizon, mae: c.mae / 1000, rmse: c.rmse / 1000, bias: c.bias / 1000 }))
  return (
    <section className="card">
      <h2>Does an earlier forecast mean a worse forecast?</h2>
      <p className="muted">Error vs how many hours ahead the forecast was made (GW)</p>
      <ResponsiveContainer width="100%" height={280}>
        <LineChart data={data}>
          <CartesianGrid stroke="var(--grid)" />
          <XAxis dataKey="horizon" unit=" h" stroke="var(--muted)" />
          <YAxis unit=" GW" stroke="var(--muted)" width={70} />
          <Tooltip contentStyle={{ background: 'var(--card)', border: '1px solid var(--border)' }}
            formatter={(v, n) => [`${v.toFixed(2)} GW`, n]} labelFormatter={(h) => `${h} h ahead`} />
          <Legend />
          <ReferenceLine x={horizon} stroke="var(--muted)" strokeDasharray="4 4" label={{ value: 'selected', fill: 'var(--muted)', fontSize: 11 }} />
          <Line dataKey="mae" name="MAE" stroke="var(--forecast)" dot={false} strokeWidth={2} />
          <Line dataKey="rmse" name="RMSE" stroke="var(--actual)" dot={false} strokeWidth={2} />
          <Line dataKey="bias" name="Bias" stroke="var(--bad)" dot={false} strokeWidth={2} />
        </LineChart>
      </ResponsiveContainer>
    </section>
  )
}
