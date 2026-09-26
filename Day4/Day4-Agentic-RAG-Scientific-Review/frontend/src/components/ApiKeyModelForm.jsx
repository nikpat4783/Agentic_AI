import { useSession } from "../context/SessionContext";

export default function ApiKeyModelForm() {
  const { apiKey, setApiKey, model, setModel, commonModels } = useSession();

  return (
    <div className="key-model-bar">
      <div className="field">
        <label htmlFor="groq-key">Groq API key</label>
        <input
          id="groq-key"
          type="password"
          placeholder="gsk_..."
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          autoComplete="off"
        />
      </div>
      <div className="field">
        <label htmlFor="model">Model</label>
        <input
          id="model"
          list="common-models"
          placeholder="e.g. openai/gpt-oss-120b"
          value={model}
          onChange={(e) => setModel(e.target.value)}
          autoComplete="off"
        />
        <datalist id="common-models">
          {commonModels.map((m) => (
            <option key={m} value={m} />
          ))}
        </datalist>
      </div>
      <p className="key-model-bar__note">
        Your key is used only for this browser session and is never stored on the server or in browser storage.
      </p>
    </div>
  );
}
