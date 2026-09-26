import ConfidenceBadge from './ConfidenceBadge.jsx'
import RationalePanel from './RationalePanel.jsx'

export default function FieldCard({ field }) {
  const { element_name, value, confidence, extraction_method, status, rationale } = field

  return (
    <article className={`field-card field-card--${status}`}>
      <header className="field-card__header">
        <h3 className="field-card__name">{element_name}</h3>
        <ConfidenceBadge status={status} confidence={confidence} />
      </header>
      <div className="field-card__value">
        {value === null || value === undefined || value === '' ? (
          <em className="field-card__empty">No value extracted</em>
        ) : (
          value
        )}
      </div>
      <div className="field-card__meta">
        <span className="pill">method: {extraction_method}</span>
      </div>
      <RationalePanel rationale={rationale} />
    </article>
  )
}
