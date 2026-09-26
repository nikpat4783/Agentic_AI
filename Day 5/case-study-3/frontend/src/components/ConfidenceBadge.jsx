// Color-coded confidence indicator. Color follows the backend's own routing
// decision (status), not a re-derived threshold guess in the UI, so the
// badge always agrees with whether a field actually needs QA.
export default function ConfidenceBadge({ status, confidence }) {
  const isStraightThrough = status === 'straight_through'
  const pct = typeof confidence === 'number' ? `${Math.round(confidence * 100)}%` : '—'

  return (
    <span
      className={`confidence-badge confidence-badge--${
        isStraightThrough ? 'green' : 'amber'
      }`}
      title={`confidence ${pct}`}
    >
      <span className="confidence-badge__dot" aria-hidden="true" />
      {isStraightThrough ? 'Straight-through' : 'Needs review'} · {pct}
    </span>
  )
}
