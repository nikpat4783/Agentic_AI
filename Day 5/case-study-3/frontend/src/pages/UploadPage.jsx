import { useEffect, useMemo, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { getSpecs, createDocument, extractDocument } from '../api/client.js'
import { useSession } from '../context/SessionContext.jsx'
import DocumentUploadForm from '../components/DocumentUploadForm.jsx'

// Known doc_types for the demo, used only as a fallback if /specs can't be
// reached — GET /specs is the real source of truth at runtime.
const FALLBACK_DOC_TYPES = ['cath_report', 'discharge_summary']

// A couple of realistic sentences per doc_type so a demo user doesn't have
// to write sample text from scratch. Keyed by doc_type; falls back to a
// generic placeholder for any doc_type not covered here.
const SAMPLE_CONTENT = {
  cath_report:
    'Cardiac catheterization report. Left ventricular ejection fraction (LVEF) ' +
    'is estimated at 55% by visual assessment. Coronary angiography shows 70% ' +
    'stenosis of the proximal left anterior descending artery. Troponin I level ' +
    'was 0.02 ng/mL, within normal limits.',
  discharge_summary:
    'Discharge summary. Patient was admitted with acute decompensated heart ' +
    'failure. Transthoracic echocardiogram showed an ejection fraction of 35%. ' +
    'Discharge diagnosis: Type 2 NSTEMI. Troponin I peaked at 1.8 ng/mL during ' +
    'admission. Patient discharged home in stable condition with cardiology ' +
    'follow-up in two weeks.',
}

function sampleFor(docType) {
  return (
    SAMPLE_CONTENT[docType] ||
    'Enter the source document text here — e.g. a narrative note mentioning ' +
      'relevant lab values, measurements, and diagnoses for this document type.'
  )
}

export default function UploadPage() {
  const navigate = useNavigate()
  const session = useSession()

  const [docTypes, setDocTypes] = useState(FALLBACK_DOC_TYPES)
  const [usingFallbackDocTypes, setUsingFallbackDocTypes] = useState(true)
  const [docType, setDocType] = useState(FALLBACK_DOC_TYPES[0])
  const [content, setContent] = useState(sampleFor(FALLBACK_DOC_TYPES[0]))
  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState(null)
  const isContentDirty = useRef(false)

  useEffect(() => {
    let cancelled = false
    getSpecs()
      .then((specs) => {
        if (cancelled) return
        const distinct = [...new Set((specs || []).map((s) => s.doc_type))]
        if (distinct.length > 0) {
          setDocTypes(distinct)
          setUsingFallbackDocTypes(false)
          setDocType(distinct[0])
          if (!isContentDirty.current) setContent(sampleFor(distinct[0]))
        }
      })
      .catch(() => {
        // Backend not reachable yet (expected while it's still being built)
        // — keep the hardcoded fallback pair, already set as initial state.
      })
    return () => {
      cancelled = true
    }
  }, [])

  const docTypeOptions = useMemo(() => docTypes, [docTypes])

  function handleDocTypeChange(next) {
    setDocType(next)
    if (!isContentDirty.current) setContent(sampleFor(next))
  }

  function handleContentChange(next) {
    isContentDirty.current = true
    setContent(next)
  }

  async function handleSubmit() {
    setError(null)
    setSubmitting(true)
    try {
      const { document_id } = await createDocument(docType, content)
      session.setDocumentId(document_id)
      await extractDocument(document_id, session.getLlmConfig())
      navigate(`/review/${document_id}`)
    } catch (err) {
      setError(
        err?.response?.data?.detail
          ? String(err.response.data.detail)
          : err.message || 'Upload/extraction failed.',
      )
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section>
      <h1>Upload a document</h1>
      <p className="page-intro">
        Submit a source document for automated extraction. Rule-based fields resolve
        instantly; narrative fields marked <code>requires_llm</code> use the LLM key
        below (BYOK, never stored).
      </p>
      {error && <div className="banner banner--error">{error}</div>}
      <DocumentUploadForm
        docTypes={docTypeOptions}
        docType={docType}
        onDocTypeChange={handleDocTypeChange}
        content={content}
        onContentChange={handleContentChange}
        onSubmit={handleSubmit}
        submitting={submitting}
        usingFallbackDocTypes={usingFallbackDocTypes}
      />
    </section>
  )
}
