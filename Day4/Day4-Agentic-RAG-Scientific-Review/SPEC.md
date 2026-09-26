# Spec — Agentic RAG for Scientific Literature Review & Drug-Discovery Intelligence

This is the project's specification: what the app is for, what it must do,
and the quality bar it's held to. It exists so a code review has a fixed
target to check against, rather than an implicit or shifting one. Keep it
in sync with reality — if the app's behavior and this file disagree, that's
a defect in whichever one is wrong.

## 1. Purpose

A demo web app for scientific-literature review and drug-discovery
intelligence. A logged-in user picks a research domain, supplies their own
LLM API key + model (BYOK), and asks a research question. An LLM-driven
agent answers by live-searching PubMed and arXiv, indexing what it finds
into a per-session vector store, and returning a cited answer streamed to
the browser.

## 2. Users

A single researcher/analyst persona per session — no multi-tenant sharing,
no admin console, no roles beyond "logged-in user." Each user brings their
own LLM provider key; the app never subsidizes or stores it.

## 3. Functional requirements

- **Auth**: register/login with a username + password; protected routes
  require a bearer JWT.
- **Domains**: a fixed registry of research domains (Logistics, Healthcare,
  Clinical Trials Statistics, Pharmacovigilance/Drug Safety), each with its
  own system-prompt framing and example questions. Adding a domain must not
  require touching more than the registry.
- **Research chat**: given a domain, a model name, a question, and a
  per-request LLM API key, the backend runs an agentic tool-calling loop
  (search PubMed / search arXiv / retrieve from the session's own vector
  index) bounded by a hard iteration cap, and streams `tool_call` /
  `tool_result` / `final` / `error` events over SSE.
- **Citations**: every factual claim in the final answer must carry a
  `[PMID:...]` or `[arXiv:...]` tag traceable to a source actually
  retrieved during that request — no uncited claims, no fabricated IDs.
- **BYOK key handling**: the LLM API key is supplied per-request by the
  client, held only in browser memory, never written to disk/localStorage/
  cookies, never logged, never persisted server-side.
- **Session isolation**: each chat session gets its own scoped vector-store
  collection; switching domains or starting a new chat gets a fresh one.

## 4. Non-functional requirements (the 10 KPIs)

These are the axes a code review should score the app against. Each has a
concrete, checkable definition — not a vibe.

1. **Accuracy / groundedness** — final answers only contain citations to
   sources actually retrieved this request; no silently-dropped citation
   formats; tool results, not prior knowledge, drive the answer.
2. **Robustness / error handling** — external-dependency failures (LLM
   provider, PubMed, arXiv) degrade gracefully (a clean error event or a
   retry), never a silent hang, a stack trace to the client, or a crashed
   process. Transient provider rate limits should be retried, not
   immediately surfaced as failure.
3. **Security** — no secret (API key, JWT, password) ever reaches a log
   line, a response body, or the database; input validated at every
   request boundary; auth enforced on every non-public route.
4. **Performance / latency** — request latency is measured (not just
   guessed at), and the app has a known behavior under concurrent load
   rather than an unknown one.
5. **Observability** — it's possible to answer "what did this specific
   request do, how long did each step take, and did anything fail" without
   attaching a debugger — via logs, traces, and metrics, not print
   statements.
6. **Test coverage** — the agent loop, the tools, the RAG pipeline, and
   auth have automated tests that run without hitting real external APIs.
7. **Maintainability / code quality** — a newcomer can find "where does X
   live and why" without archaeology; one-of-everything architecture, no
   speculative abstraction, comments explain WHY not WHAT.
8. **Cost awareness** — the app doesn't burn the user's LLM budget faster
   than the task requires (bounded agent iterations, no redundant calls),
   and load/cost-incurring test paths are opt-in and clearly labeled.
9. **Documentation** — a new contributor or reviewer can learn how the
   system fits together from written material, not just by reading every
   file.
10. **Usability / operability** — the app can be brought up locally with a
    small number of documented commands, and the "getting stuck" failure
    modes have documented explanations (e.g. what a given provider error
    actually means).

## 5. Explicit non-goals

- No multi-user data sharing, no persistent knowledge base across sessions
  (the vector store is deliberately ephemeral).
- No first-party hosting of LLM credentials — BYOK is a permanent design
  choice, not a placeholder for a future server-side key.
- No mobile app, no offline mode.

## 6. Where to look

See `README.md` for setup, `knowledge-vault/` for a fuller architectural
walkthrough, and `reports/` for point-in-time test/review snapshots. This
file is the durable spec; those are either instructions or dated evidence.
