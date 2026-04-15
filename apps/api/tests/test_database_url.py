from app.db import normalize_database_url


def test_normalize_database_url_keeps_psycopg_urls() -> None:
    url = "postgresql+psycopg://user:pass@localhost:5432/jobfocus"
    assert normalize_database_url(url) == url


def test_normalize_database_url_upgrades_postgresql_scheme() -> None:
    assert (
        normalize_database_url("postgresql://user:pass@db.example.com:5432/jobfocus")
        == "postgresql+psycopg://user:pass@db.example.com:5432/jobfocus"
    )


def test_normalize_database_url_upgrades_postgres_scheme() -> None:
    assert (
        normalize_database_url("postgres://user:pass@db.example.com:5432/jobfocus")
        == "postgresql+psycopg://user:pass@db.example.com:5432/jobfocus"
    )


def test_normalize_database_url_keeps_sqlite_urls() -> None:
    url = "sqlite:///./jobfocus.db"
    assert normalize_database_url(url) == url
