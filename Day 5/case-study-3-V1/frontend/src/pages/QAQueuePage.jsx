import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { getQaQueue, correctField } from '../api/client.js'
import QACorrectionForm from '../components/QACorrectionForm.jsx'

export default function QAQueuePage() {
  const [queue, setQueue] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [submittingId, setSubmittingId] = useState(null)
  const [successMessage, setSuccessMessage] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const result = await getQaQueue()
      setQueue(result)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load QA queue.')
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    load()
  }, [load])

  async function handleCorrect(item, correctedValue, abstractorId) {
    setSubmittingId(item.field_id)
    setError(null)
    try {
      await correctField(item.field_id, correctedValue, abstractorId)
      setQueue((prev) => prev.filter((q) => q.field_id !== item.field_id))
      setSuccessMessage(`Corrected "${item.element_name}" for document ${item.document_id}.`)
      setTimeout(() => setSuccessMessage(null), 4000)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Correction failed.')
    } finally {
      setSubmittingId(null)
    }
  }

  return (
    <section>
      <h1>QA queue</h1>
      <p className="page-intro">
        Fields flagged below the confidence threshold, across all documents. Correct
        each value and it drops off this list.
      </p>

      {error && <div className="banner banner--error">{error}</div>}
      {successMessage && <div className="banner banner--success">{successMessage}</div>}

      <div className="toolbar">
        <button type="button" onClick={load} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
      </div>

      {loading ? (
        <p>Loading queue…</p>
      ) : queue.length === 0 ? (
        <p>Nothing pending — every field is resolved.</p>
      ) : (
        <ul className="qa-queue-list">
          {queue.map((item) => (
            <li key={item.field_id} className="qa-queue-item">
              <div className="qa-queue-item__header">
                <h3>{item.element_name}</h3>
                <span className="pill">confidence {Math.round(item.confidence * 100)}%</span>
              </div>
              <p className="qa-queue-item__doc">
                Document{' '}
                <Link to={`/review/${item.document_id}`}>{item.document_id}</Link>
              </p>
              <p className="qa-queue-item__current">
                Current value: {item.current_value ?? <em>none</em>}
              </p>
              <details className="qa-queue-item__excerpt">
                <summary>Source excerpt</summary>
                <p>{item.source_excerpt}</p>
              </details>
              <details className="qa-queue-item__excerpt">
                <summary>Rationale</summary>
                <p>{item.rationale}</p>
              </details>
              <QACorrectionForm
                submitting={submittingId === item.field_id}
                onSubmit={(correctedValue, abstractorId) =>
                  handleCorrect(item, correctedValue, abstractorId)
                }
              />
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
