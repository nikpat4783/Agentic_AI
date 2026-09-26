import { useCallback, useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getFields, getAccuracyAudit } from '../api/client.js'
import FieldCard from '../components/FieldCard.jsx'

export default function ExtractionReviewPage() {
  const { documentId } = useParams()
  const [fields, setFields] = useState([])
  const [audit, setAudit] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [fieldsResult, auditResult] = await Promise.all([
        getFields(documentId),
        getAccuracyAudit(documentId).catch(() => null),
      ])
      setFields(fieldsResult)
      setAudit(auditResult)
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || 'Failed to load fields.')
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    load()
  }, [load])

  const pendingCount = fields.filter((f) => !f.resolved).length
  const allResolved = fields.length > 0 && pendingCount === 0

  return (
    <section>
      <h1>Extraction review</h1>
      <p className="page-intro">
        Document <code>{documentId}</code>
      </p>

      {error && <div className="banner banner--error">{error}</div>}

      {audit && (
        <div className="stats-strip">
          <div className="stat">
            <span className="stat__value">
              {Math.round(audit.straight_through_rate * 100)}%
            </span>
            <span className="stat__label">Straight-through rate</span>
          </div>
          <div className="stat">
            <span className="stat__value">{audit.total_fields}</span>
            <span className="stat__label">Total fields</span>
          </div>
          <div className="stat">
            <span className="stat__value">{audit.straight_through_count}</span>
            <span className="stat__label">Straight-through</span>
          </div>
          <div className="stat">
            <span className="stat__value">{audit.qa_count}</span>
            <span className="stat__label">Needs QA</span>
          </div>
        </div>
      )}

      {!loading && fields.length > 0 && (
        <div className={`banner ${pendingCount > 0 ? 'banner--warning' : 'banner--success'}`}>
          {pendingCount > 0
            ? `${pendingCount} of ${fields.length} fields need review. Correct them on the `
            : `All ${fields.length} fields are resolved.`}
          {pendingCount > 0 && <Link to="/qa">QA queue</Link>}
          {pendingCount > 0 && ' before building a submission.'}
        </div>
      )}

      <div className="toolbar">
        <button type="button" onClick={load} disabled={loading}>
          {loading ? 'Refreshing…' : 'Refresh'}
        </button>
        <Link
          to={`/submission/${documentId}`}
          className={`button-link ${!allResolved ? 'button-link--disabled' : ''}`}
          aria-disabled={!allResolved}
          title={
            allResolved
              ? 'Build the submission record'
              : 'Disabled: resolve every unresolved field first (mirrors the backend precondition)'
          }
          onClick={(e) => {
            if (!allResolved) e.preventDefault()
          }}
        >
          Build submission
        </Link>
      </div>

      {loading ? (
        <p>Loading fields…</p>
      ) : fields.length === 0 ? (
        <p>No fields found for this document.</p>
      ) : (
        <div className="field-card-grid">
          {fields.map((field) => (
            <FieldCard key={field.field_id} field={field} />
          ))}
        </div>
      )}
    </section>
  )
}
