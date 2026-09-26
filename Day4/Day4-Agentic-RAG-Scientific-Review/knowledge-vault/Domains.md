#domains #backend

# Domains

`backend/app/domains/config.py` — `DOMAIN_REGISTRY`, a dict of
`DomainConfig` entries: `id`, `name`, `description`, `system_prompt_suffix`
(appended to [[Prompt-Engineering|the base system prompt]] to steer the
agent), `example_questions`.

## Current domains

- `logistics` — Logistics
- `healthcare` — Healthcare
- `clinical_trials_stats` — Clinical Trials Statistics
- `pharmacovigilance` — Pharmacovigilance / Drug Safety

Served read-only via `GET /domains` ([[Backend]]).

## Adding a new domain

Don't hand-edit `config.py` — use the `add_domain` tool on the
`app-dev-orchestrator` MCP server (`mcp-server/server.py`), which validates
the `domain_id` (lowercase snake_case, must not already exist) before doing
text-surgery on the file. The running backend needs a restart to pick up
the change (no hot-reload of `DOMAIN_REGISTRY`).

## Known gap

`session_id` (used to pick which domain's Chroma collection to read/write)
has no length/charset validation on the request schema — an empty/huge/odd
value produces an opaque exception deep in the agent loop instead of a
clean 400 (`reports/2026-09-19-test-and-review.md`).
