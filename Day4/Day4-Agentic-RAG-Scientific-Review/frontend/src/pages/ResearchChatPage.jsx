import { useEffect, useRef, useState } from "react";
import { Navigate, useNavigate } from "react-router-dom";
import { streamResearch } from "../api/research";
import ApiKeyModelForm from "../components/ApiKeyModelForm";
import ChatMessage from "../components/ChatMessage";
import { useAuth } from "../context/AuthContext";
import { useSession } from "../context/SessionContext";

export default function ResearchChatPage() {
  const { domain, apiKey, model, sessionId, startNewChat } = useSession();
  const { token, logout } = useAuth();
  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [question, setQuestion] = useState("");
  const [busy, setBusy] = useState(false);
  const [formError, setFormError] = useState("");
  const abortRef = useRef(null);

  useEffect(() => {
    return () => abortRef.current?.abort();
  }, []);

  if (!domain) {
    return <Navigate to="/domains" replace />;
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setFormError("");

    if (!apiKey.trim()) {
      setFormError("Enter your Groq API key above before asking a question.");
      return;
    }
    if (!model.trim()) {
      setFormError("Enter or select a model above before asking a question.");
      return;
    }
    if (!question.trim()) return;

    const userMessage = { role: "user", content: question };
    const assistantMessage = { role: "assistant", steps: [], content: "", pending: true };
    setMessages((prev) => [...prev, userMessage, assistantMessage]);
    setQuestion("");
    setBusy(true);

    const controller = new AbortController();
    abortRef.current = controller;

    function updateAssistant(patch) {
      setMessages((prev) => {
        const next = [...prev];
        const idx = next.length - 1;
        next[idx] = { ...next[idx], ...patch };
        return next;
      });
    }

    try {
      await streamResearch({
        domainId: domain.id,
        model,
        question: userMessage.content,
        sessionId,
        apiKey,
        jwt: token,
        signal: controller.signal,
        onEvent(event) {
          if (event.type === "tool_call" || event.type === "tool_result") {
            setMessages((prev) => {
              const next = [...prev];
              const idx = next.length - 1;
              next[idx] = { ...next[idx], steps: [...next[idx].steps, event] };
              return next;
            });
          } else if (event.type === "final") {
            updateAssistant({
              content: event.answer,
              citations: event.citations,
              incomplete: event.incomplete,
              pending: false,
            });
          } else if (event.type === "error") {
            updateAssistant({ error: event.message, pending: false });
          }
        },
      });
    } catch (err) {
      if (err.name !== "AbortError") {
        updateAssistant({ error: err.message || "Something went wrong.", pending: false });
      }
    } finally {
      updateAssistant({ pending: false });
      setBusy(false);
    }
  }

  function handleNewChat() {
    startNewChat();
    setMessages([]);
  }

  return (
    <div className="page">
      <header className="page-header">
        <div>
          <h1>{domain.name}</h1>
          <p className="page-subtitle">{domain.description}</p>
        </div>
        <div className="page-header__actions">
          <button type="button" onClick={() => navigate("/domains")}>
            Switch domain
          </button>
          <button type="button" onClick={handleNewChat}>
            New chat
          </button>
          <button type="button" onClick={logout}>
            Log out
          </button>
        </div>
      </header>

      <ApiKeyModelForm />

      <div className="chat-window">
        {messages.length === 0 && (
          <div className="chat-empty">
            <p>Try one of these:</p>
            <ul>
              {domain.example_questions.map((q) => (
                <li key={q}>
                  <button type="button" onClick={() => setQuestion(q)}>
                    {q}
                  </button>
                </li>
              ))}
            </ul>
          </div>
        )}
        {messages.map((m, i) => (
          <ChatMessage key={i} message={m} />
        ))}
      </div>

      <form className="chat-input" onSubmit={handleSubmit}>
        <input
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Ask a research question…"
          disabled={busy}
        />
        <button type="submit" disabled={busy}>
          {busy ? "Researching…" : "Ask"}
        </button>
      </form>
      {formError && <p className="form-error">{formError}</p>}
    </div>
  );
}
