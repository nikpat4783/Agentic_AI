"""Centralized configuration for the Carta extraction backend.

All settings are read from environment variables (see `.env.example`), with
sane defaults for local dev. Nothing secret (LLM API keys) lives here -
those are BYOK, supplied per-request and never persisted.
"""
from __future__ import annotations

import os
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent.parent


class Settings:
    # CORS
    cors_origin: str = os.getenv("CORS_ORIGIN", "http://localhost:5174")

    # Auth (single hardcoded demo admin account, not a real user system -
    # see app/auth.py; tokens are in-memory only, never persisted).
    admin_username: str = os.getenv("ADMIN_USERNAME", "admin")
    admin_password: str = os.getenv("ADMIN_PASSWORD", "admin1234")

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL", f"sqlite:///{BACKEND_DIR / 'app.db'}"
    )

    # RAG / Chroma
    chroma_persist_dir: str = os.getenv(
        "CHROMA_PERSIST_DIR", str(BACKEND_DIR / "chroma_data")
    )
    chroma_collection_name: str = os.getenv(
        "CHROMA_COLLECTION_NAME", "data_element_specs"
    )
    embedding_model_name: str = os.getenv(
        "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
    )
    specs_dir: str = os.getenv("SPECS_DIR", str(BACKEND_DIR / "app" / "rag" / "specs"))

    # LLM (BYOK defaults - never a real key here)
    default_llm_base_url: str = os.getenv(
        "DEFAULT_LLM_BASE_URL", "https://api.groq.com/openai/v1/chat/completions"
    )
    # llama-3.1-8b-instant was deprecated by Groq (shutdown 2026-08-16);
    # openai/gpt-oss-120b is the requested default reasoning model for the
    # demo (gpt-oss-20b remains a valid override for lower-latency runs).
    default_llm_model: str = os.getenv("DEFAULT_LLM_MODEL", "openai/gpt-oss-120b")
    llm_timeout_seconds: float = float(os.getenv("LLM_TIMEOUT_SECONDS", "20"))

    # Observability
    otel_service_name: str = os.getenv("OTEL_SERVICE_NAME", "carta-extraction-backend")
    otel_exporter_endpoint: str = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT", "localhost:4327"
    )
    otel_enabled: bool = os.getenv("OTEL_ENABLED", "true").lower() != "false"


settings = Settings()
