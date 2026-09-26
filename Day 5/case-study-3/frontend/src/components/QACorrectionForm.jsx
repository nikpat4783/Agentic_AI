import { useState } from 'react'

// corrected value + abstractor id, posted to POST /qa/{field_id}/correct by
// the parent (QAQueuePage), which owns removing the item from the list on
// success. This form never overwrites the original model value client-side —
// it only submits a correction for the backend to record.
export default function QACorrectionForm({ onSubmit, submitting }) {
  const [correctedValue, setCorrectedValue] = useState('')
  const [abstractorId, setAbstractorId] = useState('demo-abstractor')

  function handleSubmit(e) {
    e.preventDefault()
    if (!correctedValue.trim()) return
    onSubmit(correctedValue.trim(), abstractorId.trim() || 'demo-abstractor')
  }

  return (
    <form className="qa-correction-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Corrected value</span>
        <input
          type="text"
          value={correctedValue}
          onChange={(e) => setCorrectedValue(e.target.value)}
          placeholder="Enter the correct value"
          required
        />
      </label>
      <label className="field">
        <span>Abstractor ID</span>
        <input
          type="text"
          value={abstractorId}
          onChange={(e) => setAbstractorId(e.target.value)}
        />
      </label>
      <button type="submit" disabled={submitting}>
        {submitting ? 'Submitting…' : 'Submit correction'}
      </button>
    </form>
  )
}
