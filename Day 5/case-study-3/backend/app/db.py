"""SQLAlchemy engine/session setup (SQLite, file `backend/app.db`)."""
from __future__ import annotations

from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import settings

connect_args = {"check_same_thread": False} if settings.database_url.startswith("sqlite") else {}

engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db() -> None:
    # Import models so they're registered on Base.metadata before create_all.
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def seed_data_element_specs() -> None:
    """Populate DataElementSpec from app.extraction.seed_specs.SEED_SPECS if
    the table is empty. SEED_SPECS is the single source of truth for the
    demo's 5 data elements (also used by external tooling, e.g. an MCP
    server's add_data_element_spec tool) - this function never inlines the
    seed dicts itself.
    """
    from app.extraction.seed_specs import SEED_SPECS
    from app.models import DataElementSpec

    db = SessionLocal()
    try:
        if db.query(DataElementSpec).count() > 0:
            return
        for spec in SEED_SPECS:
            db.add(DataElementSpec(**spec))
        db.commit()
    finally:
        db.close()
