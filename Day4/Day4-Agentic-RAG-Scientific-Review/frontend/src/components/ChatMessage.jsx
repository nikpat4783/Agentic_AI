import AgentStepTrace from "./AgentStepTrace";
import CitationList from "./CitationList";

export default function ChatMessage({ message }) {
  if (message.role === "user") {
    return (
      <div className="chat-message chat-message--user">
        <div className="chat-message__bubble">{message.content}</div>
      </div>
    );
  }

  return (
    <div className="chat-message chat-message--assistant">
      <AgentStepTrace steps={message.steps} />
      {message.error && <div className="chat-message__error">{message.error}</div>}
      {message.content && (
        <div className="chat-message__bubble">
          {message.content}
          {message.incomplete && (
            <p className="chat-message__incomplete-note">
              (Stopped early after the step budget — this answer may be incomplete.)
            </p>
          )}
        </div>
      )}
      {message.pending && <div className="chat-message__pending">Thinking…</div>}
      <CitationList citations={message.citations} />
    </div>
  );
}
