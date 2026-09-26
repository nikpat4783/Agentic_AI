#frontend

# Frontend

React 19 + Vite 7 (plain JS, no TypeScript, no CSS framework), dev server on
`:5174` (`vite --port 5174` baked into the `dev` script), talking to the
backend at `VITE_API_BASE_URL` (default `http://localhost:8002`).

## Pages/flow

- **LoginPage** (`/login`, not protected) — username/password form against
  the demo account (`admin`/`admin1234`, shown as an on-screen hint), calls
  `AuthContext.login()`, navigates to `/` on success, shows "Invalid
  username or password." on 401.
- Every other route (`/`, `/review/:documentId`, `/qa`,
  `/submission/:documentId`) is wrapped in `ProtectedRoute`, which
  redirects to `/login` when not authenticated. A "Log out" link appears in
  the nav once logged in.
- **UploadPage** (`/`) — loads `GET /specs` to derive available `doc_type`s,
  labeled **"Domain"** in the UI with friendlier display names
  (`cath_report` → "Cardiology — Cath Report", `discharge_summary` →
  "General — Discharge Summary") while the underlying value sent to the
  backend is unchanged — a labeling change, not a new domain-registry
  concept. Falls back to a hardcoded pair with an on-screen note if
  `/specs` is unreachable. Pre-fills a realistic sample document per
  domain, an `ApiKeyInput` for the BYOK LLM key (password-type field,
  explicit "never stored" note, placeholder now reads
  `openai/gpt-oss-120b (default if left blank)` — the backend's own
  default already is that model when the field is left empty, so the
  input is intentionally not pre-filled, keeping the model default
  single-sourced server-side), submits `POST /documents` →
  `POST .../extract`, navigates to the review page.
- **ExtractionReviewPage** (`/review/:documentId`) — every field as a
  `FieldCard` with a `ConfidenceBadge` colored strictly off the backend's
  own `status` (green=`straight_through`, amber=`pending_qa` — not a
  re-derived threshold guess) and an expandable `RationalePanel` (native
  `<details>`, not a tooltip) showing the RAG-grounded rationale. A stats
  strip surfaces the live `GET .../accuracy-audit` numbers. "Build
  submission" is disabled with an explanatory title until zero fields are
  `pending_qa` — mirrors the backend's own precondition so the user gets
  instant feedback instead of a rejected request.
- **QAQueuePage** (`/qa`) — `GET /qa/queue`, each item shows its
  `source_excerpt` + rationale, a correction form posts to
  `POST /qa/{field_id}/correct` and removes the item with an inline success
  banner.
- **SubmissionPage** (`/submission/:documentId`) — calls
  `POST .../submission`; renders the resulting record as a key/value table,
  or the 409 error's unresolved-fields list with a retry/back-link.

## BYOK key handling

The LLM API key lives only in `SessionContext` React state — never
`localStorage`/`sessionStorage`/cookies, never logged. It's sent in the JSON
body of the single `POST .../extract` call that needs it (the fixed API
contract specifies body, not header — see the build report / [[Backend]]
for the contract), never set as an axios default, so it can't leak into an
unrelated request.

## Session token handling

`AuthContext` holds the login token only in React state, mirrored into a
module-level variable in `api/client.js` (`setAuthToken()`) that a single
axios request interceptor reads to attach `Authorization: Bearer <token>`
to every outgoing request — never written to `localStorage`/
`sessionStorage`/cookies, same rule as the BYOK key. This interceptor
approach meant no individual page/API-call site needed to change to carry
the token — only `client.js`, `main.jsx` (added `AuthProvider`), and
`App.jsx` (added the `/login` route + `ProtectedRoute` wrapping) did.

## Verified

`npm install` (0 vulnerabilities) and `npm run build` both succeeded; the
dev server was confirmed to serve the real HTML shell via `curl`. No
browser/visual check was performed — no headless-browser tool is available
in this environment, so the actual click-through happens in [[Demo]] against
a person's real browser, not as an automated check here.
