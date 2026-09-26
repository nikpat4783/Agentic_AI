import { useCallback, useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { buildSubmission } from '../api/client.js'

export default function SubmissionPage() {
  const { documentId } = useParams()
  const [result, setResult] = useState(null)
  const [unresolvedDetail, setUnresolvedDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  const attempt = useCallback(async () => {
    setLoading(true)
    setError(null)
    setUnresolvedDetail(null)
    setResult(null)
    try {
      const data = await buildSubmission(documentId)
      setResult(data)
    } catch (err) {
      if (err?.response?.status === 409) {
        setUnresolvedDetail(err.response.data?.detail)
      } else {
        setError(err?.response?.data?.detail || err.message || 'Submission build failed.')
      }
    } finally {
      setLoading(false)
    }
  }, [documentId])

  useEffect(() => {
    attempt()
  }, [attempt])

  return (
    <section>
      <h1>Submission</h1>
      <p className="page-intro">
        Document <code>{documentId}</code>
      </p>

      {loading && <p>Building submission…</p>}

      {error && <div className="banner banner--error">{error}</div>}

      {unresolvedDetail && (
        <div className="banner banner--warning">
          <p>The backend refused to build the submission — unresolved fields remain:</p>
          <p className="unresolved-detail">
            {Array.isArray(unresolvedDetail) ? unresolvedDetail.join(', ') : String(unresolvedDetail)}
          </p>
          <p>
            Resolve them on the <Link to={`/review/${documentId}`}>review page</Link> or in the{' '}
            <Link to="/qa">QA queue</Link>, then retry.
          </p>
          <button type="button" onClick={attempt}>
            Retry
          </button>
        </div>
      )}

      {result && (
        <div>
          <div className="banner banner--success">
            Submission <code>{result.submission_id}</code> — status: {result.status}
          </div>
          <table className="record-table">
            <thead>
              <tr>
                <th>Element</th>
                <th>Value</th>
              </tr>
            </thead>
            <tbody>
              {Object.entries(result.record || {}).map(([key, value]) => (
                <tr key={key}>
                  <td>{key}</td>
                  <td>{value === null || value === undefined ? <em>—</em> : String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  )
}
