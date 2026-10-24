// Flags a large average bias. The "even under 4 hours ahead" observation is
// only shown when the horizon curve's 0 h point (forecasts published 0.5–3.5 h
// before delivery in this data) has a bias of the same sign and size.
export default function BiasNote({ m, curve }) {
  if (!m?.count || Math.abs(m.bias) <= 500) return null
  const below = m.bias < 0
  const shortLead = curve?.find((c) => c.horizon === 0)
  const persists = shortLead && Math.abs(shortLead.bias) > 500 && (shortLead.bias < 0) === below
  return (
    <p className="note">
      Wind came in {below ? 'below' : 'above'} forecast on average
      {persists
        ? ', even for forecasts made under 4 hours ahead. This points to a difference between what the two '
          + 'datasets measure (for example, curtailed wind or different wind farms counted) rather than only '
          + 'forecast skill.'
        : '.'}
      {' '}Treat the bias as a systematic adjustment.
    </p>
  )
}
