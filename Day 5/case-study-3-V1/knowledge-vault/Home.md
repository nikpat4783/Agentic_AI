#home

# Carta Healthcare — Knowledge Vault

A demo web app that automates extraction of structured clinical data
elements from source documents, routes only low-confidence extractions to a
human abstractor, and builds a submission-ready structured record —
demonstrating the **66% faster / 99% accuracy** claim from
[Case Study 3](../../03-carta-healthcare.md) end to end.

## Subsystems

- [[Backend]] — FastAPI app, routers, models, config
- [[Extraction-Pipeline]] — the pluggable rule/LLM extractor registry and
  confidence routing
- [[RAG-Engine]] — the Chroma + sentence-transformers index over registry
  data-element specs that grounds every confidence decision
- [[Frontend]] — React/Vite UI, confidence-highlighted review flow
- [[MCP-Servers]] — the official `fetch` server plus this project's custom
  `app-dev-orchestrator`
- [[Observability]] — OpenTelemetry → Grafana/Prometheus/Loki/Tempo
- [[Load-Testing]] — k6 scenarios and the k6 Grafana dashboard
- [[Prompt-Engineering]] — LLM-extractor/guardrail prompt iteration log
- [[Demo]] — click-through script for showing this to a first user

## Where things run

| Thing | URL |
|---|---|
| Frontend | http://localhost:5174 |
| Backend API (docs) | http://localhost:8002/docs |
| Grafana | http://localhost:3010 |
| Prometheus | http://localhost:9091 |

## How this vault was built

Generated as part of a full 20-step build (Claude Code project scaffolding →
subagents → RAG → MCP servers → observability → load testing → this vault →
a graphify knowledge graph → prompt tuning → demo) implementing the HLD/LLD
at `../../03-carta-healthcare.md`. See `../reports/` at the project root for
the underlying test/review reports that fed into this, and
`../graphify-out/` for a generated knowledge graph of the codebase itself.
