#agent #backend

# Agent Orchestrator

`backend/app/agent/orchestrator.py` — the tool-calling loop behind
`POST /research/stream`.

## Flow

1. System prompt built via `build_system_prompt(domain)` in
   `backend/app/agent/prompts.py` — see [[Prompt-Engineering]].
2. Calls the LLM through `GroqClient.chat_completion`
   (`backend/app/agent/groq_client.py`) — a raw `httpx.AsyncClient`
   POST to `https://api.groq.com/openai/v1/chat/completions`, no SDK. This is
   why `HTTPXClientInstrumentor` (see [[Observability]]) is enough to trace
   every LLM/PubMed/arXiv call with zero changes to this client.
3. If the model returns tool calls, each is dispatched via `_dispatch_tool`
   to `search_pubmed`, `search_arxiv`, or `retrieve_from_index`
   (`backend/app/agent/tools/`), and the result is appended back as a
   `{"role": "tool", ...}` message.
4. Loops until the model answers without calling a tool, or
   `max_agent_iterations` (from settings) is hit, at which point a final
   call is forced with `tool_choice="none"`.
5. Streams `{type: "tool_call"|"tool_result"|"final"|"error", ...}` frames
   back over SSE.

## Tools (`backend/app/agent/tools/schemas.py`)

Three tools: `search_pubmed` ("Prefer this for clinical, health-services,
adverse-event, and biomedical questions"), `search_arxiv`, and
`retrieve_from_index` (queries the session's own [[RAG-Pipeline]] Chroma
collection).

## Known correctness issues (from `reports/2026-09-19-test-and-review.md`)

- Citation regex drops pre-2007 arXiv IDs (no `/` allowed) —
  `backend/app/agent/orchestrator.py`.
- `max_results: null` from the model isn't defaulted, only a *missing* key
  is — same file.
- Malformed tool-call JSON fails silently (no log) unlike the sibling
  `GroqError` path.

These are correctness bugs, not prompt issues — tracked separately from
[[Prompt-Engineering]], which only covers the prompt text itself.

## Observability hooks

A span per tool-dispatch iteration (`agent.tool_iteration`, tagged with
tool name / domain / iteration number) plus an `app_agent_loop_iterations`
histogram recording total iterations per request — added as part of
[[Observability]], visible on the "Agentic RAG - App Overview" Grafana
dashboard and in Tempo traces.
