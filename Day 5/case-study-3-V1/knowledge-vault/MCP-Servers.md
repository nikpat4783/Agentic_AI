#mcp #tooling

# MCP servers

`.mcp.json` at the project root registers two servers.

## `fetch` (external, official)

```json
"fetch": { "type": "stdio", "command": "uvx", "args": ["mcp-server-fetch"] }
```

The official `mcp-server-fetch` package (run via `uvx`, no local install
step) — general-purpose URL fetching for agents working in this repo who
need to check a live doc page.

## `app-dev-orchestrator` (custom, this project)

`mcp-server/server.py`, Python MCP SDK (`mcp==2.2.0`). Reusable orchestration
tools so a Claude Code session (or any MCP client) can drive this project
without hand-running shell commands every time:

- `start_dev_servers` / `stop_dev_servers` — backend `:8002` + frontend
  `:5174` as background processes, tracked in `.dev-pids.json`, logs in
  `.dev-logs/`.
- `run_backend_tests` / `run_frontend_build` — pytest / `npm run build`.
- `start_observability_stack` / `stop_observability_stack` — `docker compose
  up -d` / `down` in `observability/` (this project's own ports/project
  name — see [[Observability]]).
- `run_load_test(scenario)` — runs the `smoke` or `extraction` k6 scenario
  (see [[Load-Testing]]), pushing metrics to this project's Prometheus.
- `list_data_element_specs` — reads live from the running backend's
  `GET /specs`, falling back to reading `backend/app/extraction/seed_specs.py`
  directly if the backend isn't up.
- `add_data_element_spec(...)` — registers a new element (appends to
  `seed_specs.py`, writes its RAG spec text under `app/rag/specs/`) without
  hand-editing pipeline code — mirrors the [[Extraction-Pipeline|"config,
  not code-fork"]] design goal.
- `scaffold_new_extractor(element_name, description)` — appends a stub
  regex-function skeleton to `rule_extractors.py` for a new rule-based
  element (still requires filling in the actual pattern by hand).

All dev-server/observability/load-test tools resolve paths relative to
`server.py`'s own location, so they work regardless of the caller's cwd.
