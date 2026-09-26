import { useSession } from '../context/SessionContext.jsx'

// BYOK LLM credentials. These live only in SessionContext (React state) —
// never localStorage/sessionStorage/cookies, never console.logged. They are
// sent only in the body of the extraction-trigger request, then forgotten by
// the network layer; this input is left blank again on every fresh page load
// by design.
export default function ApiKeyInput() {
  const { llmApiKey, setLlmApiKey, llmModel, setLlmModel, llmBaseUrl, setLlmBaseUrl } =
    useSession()

  return (
    <fieldset className="api-key-input">
      <legend>LLM API key (BYOK)</legend>
      <p className="api-key-input__note">
        Only used for this extraction request, never stored or logged. Required only for
        narrative fields that need an LLM extractor — rule-based fields work without it.
      </p>
      <label className="field">
        <span>API key</span>
        <input
          type="password"
          autoComplete="off"
          placeholder="sk-..."
          value={llmApiKey}
          onChange={(e) => setLlmApiKey(e.target.value)}
        />
      </label>
      <div className="field-row">
        <label className="field">
          <span>Model (optional)</span>
          <input
            type="text"
            autoComplete="off"
            placeholder="openai/gpt-oss-120b (default if left blank)"
            value={llmModel}
            onChange={(e) => setLlmModel(e.target.value)}
          />
        </label>
        <label className="field">
          <span>Base URL (optional)</span>
          <input
            type="text"
            autoComplete="off"
            placeholder="e.g. https://api.openai.com/v1"
            value={llmBaseUrl}
            onChange={(e) => setLlmBaseUrl(e.target.value)}
          />
        </label>
      </div>
    </fieldset>
  )
}
