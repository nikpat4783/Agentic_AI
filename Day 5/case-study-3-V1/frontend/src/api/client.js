import axios from 'axios'

const baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8002'

// A single axios instance for the whole app. Nothing sensitive (the BYOK LLM
// key) is ever set on its defaults/headers — the key is passed explicitly,
// per-call, only in the body of the one extraction-trigger request that
// needs it, so it can never leak into an unrelated request by accident.
const client = axios.create({ baseURL })

// The session auth token (from POST /auth/login) lives ONLY in AuthContext
// React state; it is never written to localStorage/sessionStorage/cookies.
// This module-level variable is just an in-memory mirror of that state, set
// via setAuthToken() from AuthContext on login/logout, so the request
// interceptor below has something synchronous to read (axios interceptors
// aren't React components and can't call useContext). It is unset again on
// logout and never persisted anywhere.
let authToken = null

export function setAuthToken(token) {
  authToken = token
}

client.interceptors.request.use((config) => {
  if (authToken) {
    config.headers = config.headers ?? {}
    config.headers.Authorization = `Bearer ${authToken}`
  }
  return config
})

export const getHealth = () => client.get('/health').then((r) => r.data)

export const getSpecs = () => client.get('/specs').then((r) => r.data)

export const createDocument = (docType, content) =>
  client.post('/documents', { doc_type: docType, content }).then((r) => r.data)

// llmConfig: { llm_api_key, llm_model, llm_base_url } | null — the fixed API
// contract carries the BYOK key in the request body for this call only.
export const extractDocument = (documentId, llmConfig) =>
  client.post(`/documents/${documentId}/extract`, llmConfig ?? {}).then((r) => r.data)

export const getFields = (documentId) =>
  client.get(`/documents/${documentId}/fields`).then((r) => r.data)

export const getQaQueue = () => client.get('/qa/queue').then((r) => r.data)

export const correctField = (fieldId, correctedValue, abstractorId) =>
  client
    .post(`/qa/${fieldId}/correct`, {
      corrected_value: correctedValue,
      abstractor_id: abstractorId,
    })
    .then((r) => r.data)

export const buildSubmission = (documentId) =>
  client.post(`/documents/${documentId}/submission`).then((r) => r.data)

export const getAccuracyAudit = (documentId) =>
  client.get(`/documents/${documentId}/accuracy-audit`).then((r) => r.data)

export default client
