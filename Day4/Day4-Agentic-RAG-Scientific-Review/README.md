# Agentic RAG for Scientific Literature Review & Drug-Discovery Intelligence

A demo web app where a logged-in user picks a research domain, supplies their own
Groq API key + model, and asks research questions that an LLM-driven agent
answers by live-searching PubMed and arXiv, indexing results into a per-session
vector store, and returning a cited answer.

## Domains

- **Logistics** — pharmaceutical supply-chain, cold-chain, and drug-distribution logistics
- **Healthcare** — healthcare delivery and health-systems literature
- **Clinical Trials Statistics** — biostatistics and clinical trial design
- **Pharmacovigilance / Drug Safety** — adverse-event monitoring and post-market surveillance

## Architecture

- **Backend**: FastAPI (`backend/`) — local JWT auth, domain registry, an agentic
  tool-calling loop over Groq's chat-completions API, PubMed/arXiv search
  tools, and a local Chroma + sentence-transformers vector store (ephemeral,
  scoped per chat session).
- **Frontend**: React + Vite (`frontend/`) — login/register, domain selection, a
  Groq API key + model input, and a research chat UI that streams the
  agent's tool calls and final cited answer over SSE.

The user's Groq API key is entered in the UI each session, held only in
browser memory (never written to disk or browser storage), and threaded through
requests via an `X-Groq-Key` header. It is never persisted or logged on
the backend.

## Running locally

```bash
make install   # creates backend/.venv and installs both sides
cp backend/.env.example backend/.env       # edit JWT_SECRET_KEY
cp frontend/.env.example frontend/.env
make dev       # runs backend (:8001) and frontend (:5173) together
```

Then open http://localhost:5173, register an account, pick a domain, enter a
Groq API key (get one at https://console.groq.com/keys) and a model (e.g.
`openai/gpt-oss-120b`), and ask a research question.

## Tests

```bash
make test
```

Backend tests cover auth, the PubMed/arXiv tool wrappers (mocked HTTP), the
vector store/indexer, chunking, and the agent orchestration loop (mocked
Groq client).
