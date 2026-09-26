import { createContext, useContext, useMemo, useState } from 'react'

// The BYOK LLM API key lives ONLY here, in React state, for the lifetime of
// this tab. It is never written to localStorage/sessionStorage/cookies and
// never logged (no console.log of session state anywhere in this app) — it
// is re-entered every page load by design. See frontend.md / SPEC.md
// (security KPI #3, BYOK requirement #3).
const SessionContext = createContext(null)

export function SessionProvider({ children }) {
  const [llmApiKey, setLlmApiKey] = useState('')
  const [llmModel, setLlmModel] = useState('')
  const [llmBaseUrl, setLlmBaseUrl] = useState('')
  // The most recently created/extracted document, so pages can link forward
  // (e.g. review -> submission) without re-threading ids through props.
  const [documentId, setDocumentId] = useState(null)

  const value = useMemo(
    () => ({
      llmApiKey,
      setLlmApiKey,
      llmModel,
      setLlmModel,
      llmBaseUrl,
      setLlmBaseUrl,
      documentId,
      setDocumentId,
      // Builds the optional body for POST /documents/{id}/extract. Empty
      // fields are sent as null rather than "" so the backend's own
      // "was a key supplied at all" check behaves as intended.
      getLlmConfig() {
        return {
          llm_api_key: llmApiKey.trim() ? llmApiKey.trim() : null,
          llm_model: llmModel.trim() ? llmModel.trim() : null,
          llm_base_url: llmBaseUrl.trim() ? llmBaseUrl.trim() : null,
        }
      },
    }),
    [llmApiKey, llmModel, llmBaseUrl, documentId],
  )

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>
}

export function useSession() {
  const ctx = useContext(SessionContext)
  if (!ctx) {
    throw new Error('useSession must be used within a SessionProvider')
  }
  return ctx
}
