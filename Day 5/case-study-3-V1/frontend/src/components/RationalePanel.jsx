// Expandable/collapsible RAG-grounded rationale — a native <details> element
// so it's keyboard/screen-reader accessible without extra JS state, and
// reads as a real explanation panel rather than a tooltip that's easy to miss.
export default function RationalePanel({ rationale }) {
  return (
    <details className="rationale-panel">
      <summary>Why this value / confidence?</summary>
      <p className="rationale-panel__text">
        {rationale || 'No rationale was returned for this field.'}
      </p>
    </details>
  )
}
