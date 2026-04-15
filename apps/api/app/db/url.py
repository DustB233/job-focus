from __future__ import annotations


def normalize_database_url(database_url: str) -> str:
    """Normalize Postgres URLs so SQLAlchemy always uses Psycopg 3."""
    if database_url.startswith("postgresql+psycopg://"):
        return database_url

    if database_url.startswith("postgres://"):
        return f"postgresql+psycopg://{database_url.removeprefix('postgres://')}"

    if database_url.startswith("postgresql://"):
        return f"postgresql+psycopg://{database_url.removeprefix('postgresql://')}"

    return database_url
