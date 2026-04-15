from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.db import normalize_database_url
from app.models import Base

_engine: Engine | None = None
_session_factory: sessionmaker[Session] | None = None


def _connect_args(database_url: str) -> dict[str, object]:
    if database_url.startswith("sqlite"):
        return {"check_same_thread": False}
    return {}


def get_engine(database_url: str | None = None) -> Engine:
    global _engine, _session_factory

    resolved_url = normalize_database_url(database_url or get_settings().database_url)
    current_url = str(_engine.url) if _engine is not None else None

    if _engine is None or current_url != resolved_url:
        _engine = create_engine(
            resolved_url,
            future=True,
            connect_args=_connect_args(resolved_url),
        )
        _session_factory = sessionmaker(bind=_engine, autoflush=False, expire_on_commit=False)

    return _engine


def get_session_factory() -> sessionmaker[Session]:
    get_engine()
    assert _session_factory is not None
    return _session_factory


def create_all_tables() -> None:
    engine = get_engine()
    Base.metadata.create_all(bind=engine)


def reset_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        _engine.dispose()
    _engine = None
    _session_factory = None


def get_db_session() -> Generator[Session, None, None]:
    session = get_session_factory()()
    try:
        yield session
    finally:
        session.close()


@contextmanager
def session_scope(database_url: str | None = None) -> Generator[Session, None, None]:
    factory = get_session_factory() if database_url is None else sessionmaker(
        bind=get_engine(database_url),
        autoflush=False,
        expire_on_commit=False,
    )
    session = factory()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
