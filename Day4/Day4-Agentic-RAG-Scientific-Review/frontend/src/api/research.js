import { fetchEventSource } from "@microsoft/fetch-event-source";
import { API_BASE_URL } from "./client";

/**
 * Streams an agentic-RAG research turn. Calls onEvent(parsedEvent) for each
 * SSE event ({type: "tool_call"|"tool_result"|"final"|"error", ...}).
 */
export async function streamResearch({ domainId, model, question, sessionId, apiKey, jwt, onEvent, signal }) {
  await fetchEventSource(`${API_BASE_URL}/research/stream`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${jwt}`,
      "X-Groq-Key": apiKey,
    },
    body: JSON.stringify({ domain_id: domainId, model, question, session_id: sessionId }),
    signal,
    openWhenHidden: true,
    async onopen(response) {
      if (!response.ok) {
        const detail = await response.text();
        throw new Error(`Request failed (${response.status}): ${detail}`);
      }
    },
    onmessage(event) {
      if (!event.data) return;
      try {
        onEvent(JSON.parse(event.data));
      } catch {
        // ignore malformed frames
      }
    },
    onerror(err) {
      // rethrow so fetchEventSource stops retrying — this is a single research turn, not a long-lived stream
      throw err;
    },
  });
}
