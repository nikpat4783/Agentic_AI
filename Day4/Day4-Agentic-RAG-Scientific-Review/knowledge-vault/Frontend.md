#frontend

# Frontend

React + Vite, served on **:5173** (`npm run dev` in `frontend/`, default
Vite port, no override in `vite.config.js`).

- API base URL: `frontend/src/api/client.js` reads
  `VITE_API_BASE_URL` (defaults to `http://localhost:8001`).
- SSE client: `frontend/src/api/research.js`, using
  `@microsoft/fetch-event-source` to POST to `/research/stream` with
  `Authorization` + `X-Groq-Key` headers, dispatching parsed
  `onmessage` frames to the UI as they arrive.
- The Groq key is entered by the user directly in the browser,
  per session, and is never persisted or logged — see [[Backend]] and
  [[Demo]].
- `App.jsx` currently ignores the `:domainId` route param on refresh —
  bookmarking `/research/logistics` bounces back to domain selection
  because `ResearchChatPage` only trusts in-memory `SessionContext` state
  (`reports/2026-09-19-test-and-review.md`).
- No automated frontend test suite exists yet (no vitest/jest configured)
  — verification here is manual/browser-driven only.

## CORS

`backend/app/main.py` configures `CORSMiddleware` with
`allow_origins` defaulting to `http://localhost:5173` (env-overridable via
`CORS_ORIGINS`). Only relevant to browser requests — [[Load-Testing]]'s k6
scripts hit the API directly and aren't subject to CORS.
