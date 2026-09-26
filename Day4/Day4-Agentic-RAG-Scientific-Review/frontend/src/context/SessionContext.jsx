import { createContext, useContext, useMemo, useState } from "react";

const SessionContext = createContext(null);

const COMMON_MODELS = [
  "openai/gpt-oss-120b",
  "openai/gpt-oss-20b",
  "llama-3.3-70b-versatile",
  "llama-3.1-8b-instant",
];

function newSessionId() {
  return crypto.randomUUID();
}

export function SessionProvider({ children }) {
  const [apiKey, setApiKey] = useState(""); // in-memory only, never persisted
  const [model, setModel] = useState("openai/gpt-oss-120b");
  const [domain, setDomain] = useState(null);
  const [sessionId, setSessionId] = useState(newSessionId());

  function selectDomain(nextDomain) {
    setDomain(nextDomain);
    setSessionId(newSessionId()); // fresh vector-store collection per domain switch
  }

  function startNewChat() {
    setSessionId(newSessionId());
  }

  const value = useMemo(
    () => ({
      apiKey,
      setApiKey,
      model,
      setModel,
      domain,
      selectDomain,
      sessionId,
      startNewChat,
      commonModels: COMMON_MODELS,
    }),
    [apiKey, model, domain, sessionId]
  );

  return <SessionContext.Provider value={value}>{children}</SessionContext.Provider>;
}

export function useSession() {
  const ctx = useContext(SessionContext);
  if (!ctx) throw new Error("useSession must be used within SessionProvider");
  return ctx;
}
