# Agentic RAG — Literature Review & Drug-Discovery Intelligence

Two-part app: `backend/` (FastAPI + agentic RAG orchestrator + Chroma) and
`frontend/` (React + Vite). See `README.md` for what it does and
`.claude/skills/dev-workflow/SKILL.md` for how to run/test/extend it.

## Subagent delegation policy

Three project subagents live in `.claude/agents/`: `backend`, `frontend`,
`p3-triage`. Delegate to them instead of doing the work directly when the
task fits their scope:

- **Backend-only work** (anything under `backend/`: routes, the agent
  orchestrator, tools, RAG pipeline, auth, tests) → delegate to `backend`.
- **Frontend-only work** (anything under `frontend/src/`: pages, components,
  context, styling, the SSE client) → delegate to `frontend`.
- **Work touching both sides** (e.g. a new endpoint plus the UI that calls
  it) → split it: delegate the backend half and frontend half as two
  self-contained briefs, in parallel when they don't depend on each other's
  output, sequentially when the frontend piece needs a finished API contract
  first.
- **Post-implementation cleanup / severity triage** (sweeping for
  cosmetic/nice-to-have issues once a feature already works and has been
  reviewed for correctness) → delegate to `p3-triage`. Never use it as the
  only review pass — it deliberately reports only the P3 backlog, not
  blocking bugs.
- **Don't delegate** requirements clarification, architecture decisions, or
  anything requiring the user's judgment call — resolve those in the main
  session (ask the user directly) first, then hand the resolved, concrete
  task to a subagent.

## Plugins

- **Internal tools**: `backend` and `frontend` subagents both carry
  `WebFetch`/`WebSearch` in addition to `Read, Write, Edit, Bash, Grep, Glob`,
  so they can check current third-party API/library docs without escalating
  back to the main session.
- **External plugin**: `pr-review-toolkit@claude-plugins-official` (from
  Anthropic's official marketplace, `.claude/settings.json` →
  `enabledPlugins`) is installed at project scope. It adds specialized PR
  review agents — use it for a deeper correctness/security pass on a pull
  request, complementary to (not a replacement for) `p3-triage`, which only
  covers the cosmetic backlog.

## Isolation & context-trimming contract (applies to all three subagents)

Each subagent's own file (`.claude/agents/*.md`) carries the full version of
this; the summary that matters for how you delegate:

- **Isolation**: a subagent invocation starts with no memory of this
  conversation. Every delegation prompt must be self-contained — concrete
  task, relevant file paths, decisions already made. Never write "as
  discussed above" into a delegation prompt.
- **Context trimming**: if a subagent is resumed many times on one long task
  (via `SendMessage`, not a fresh `Agent` call), it should keep its most
  recent 8-10 exchanges verbatim and compress everything older into a single
  running summary sized to roughly 12-15% of its context budget — file
  paths, decisions, and open threads only, not a transcript. This is a
  behavioral instruction each agent follows on its own; there is no
  Claude Code setting that enforces a context-percentage budget directly.
