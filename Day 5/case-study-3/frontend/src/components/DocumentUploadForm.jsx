import ApiKeyInput from './ApiKeyInput.jsx'

// Friendlier display names for the underlying doc_type value — labeling
// only, the value sent to the backend is unchanged. Any doc_type not listed
// here (e.g. a new one added via /specs) just falls back to its raw value.
const DOC_TYPE_LABELS = {
  cath_report: 'Cardiology — Cath Report',
  discharge_summary: 'General — Discharge Summary',
}

function labelForDocType(dt) {
  return DOC_TYPE_LABELS[dt] || dt
}

export default function DocumentUploadForm({
  docTypes,
  docType,
  onDocTypeChange,
  content,
  onContentChange,
  onSubmit,
  submitting,
  usingFallbackDocTypes,
}) {
  function handleSubmit(e) {
    e.preventDefault()
    onSubmit()
  }

  return (
    <form className="document-upload-form" onSubmit={handleSubmit}>
      <label className="field">
        <span>Domain</span>
        <select value={docType} onChange={(e) => onDocTypeChange(e.target.value)}>
          {docTypes.map((dt) => (
            <option key={dt} value={dt}>
              {labelForDocType(dt)}
            </option>
          ))}
        </select>
      </label>
      {usingFallbackDocTypes && (
        <p className="hint">
          Could not load domains from <code>GET /specs</code> — showing a hardcoded
          fallback pair. This list should track <code>/specs</code> once the backend is up.
        </p>
      )}

      <label className="field">
        <span>Document content</span>
        <textarea
          rows={8}
          value={content}
          onChange={(e) => onContentChange(e.target.value)}
          placeholder="Paste or edit the document text…"
        />
      </label>

      <ApiKeyInput />

      <button type="submit" disabled={submitting || !content.trim()}>
        {submitting ? 'Uploading & extracting…' : 'Upload & extract'}
      </button>
    </form>
  )
}
