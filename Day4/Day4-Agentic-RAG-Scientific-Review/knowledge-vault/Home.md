#home

# Agentic RAG — Knowledge Vault

A demo web app where a logged-in user picks a research domain, supplies
their own Groq API key + model, and asks a question that an LLM agent
answers by live-searching PubMed/arXiv, indexing results into a per-session
Chroma vector store, and returning a cited answer via SSE streaming.

## Subsystems

- [[Backend]] — FastAPI app, routers, auth, config
- [[Agent-Orchestrator]] — the tool-calling loop that drives Groq
- [[RAG-Pipeline]] — chunking, embeddings, Chroma, reranking
- [[Domains]] — the four research domains and how to add a new one
- [[Auth]] — JWT login/register flow
- [[Frontend]] — React/Vite UI, SSE client
- [[Observability]] — OpenTelemetry → Grafana/Prometheus/Loki/Tempo
- [[Load-Testing]] — k6 scenarios and the k6 Grafana dashboard
- [[Prompt-Engineering]] — system-prompt iteration log
- [[Demo]] — click-through script for showing this to a first user

## Where things run

| Thing | URL |
|---|---|
| Frontend | http://localhost:5173 |
| Backend API (docs) | http://localhost:8001/docs |
| Grafana | http://localhost:3000 |
| Prometheus | http://localhost:9090 |

## How this vault was built

Generated from a live read of the codebase (not boilerplate) as part of an
effort to add observability, load testing, a knowledge graph
(`graphify-out/` at the repo root, via the `graphify` skill), and prompt
tuning to the POC. See `reports/` at the repo root for the underlying
test/review reports that fed into this.
