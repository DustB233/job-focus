"""Promote job sources into a multi-source registry.

Revision ID: 20260415_0002
Revises: 20260412_0001
Create Date: 2026-04-15 10:30:00
"""

from __future__ import annotations

import json
from collections import defaultdict
from urllib.parse import quote

from alembic import op
import sqlalchemy as sa


revision = "20260415_0002"
down_revision = "20260412_0001"
branch_labels = None
depends_on = None


def _decode_payload(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except json.JSONDecodeError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _infer_identifier(slug: str, jobs: list[dict[str, object]]) -> str | None:
    key = "boardToken" if slug == "greenhouse" else "siteName" if slug == "lever" else None
    if key is None:
        return None

    for job in jobs:
        payload = _decode_payload(job.get("raw_payload"))
        identifier = payload.get(key)
        if isinstance(identifier, str) and identifier.strip():
            return identifier.strip()
    return None


def _default_base_url(
    slug: str,
    external_identifier: str | None,
    existing_base_url: str | None,
) -> str | None:
    if slug == "greenhouse" and external_identifier:
        return f"https://boards-api.greenhouse.io/v1/boards/{quote(external_identifier, safe='')}"
    if slug == "lever" and external_identifier:
        return f"https://api.lever.co/v0/postings/{quote(external_identifier, safe='')}?mode=json"
    if slug == "ashby":
        return existing_base_url or "https://jobs.ashbyhq.com"
    return existing_base_url


def _default_display_name(
    slug: str,
    external_identifier: str | None,
    existing_display_name: str,
) -> str:
    generic_labels = {
        "greenhouse": "Greenhouse",
        "lever": "Lever",
        "ashby": "Ashby",
        "manual": "Manual Link",
    }
    generic_label = generic_labels.get(slug, slug.replace("_", " ").title())
    if existing_display_name.strip() and existing_display_name.strip().lower() != generic_label.lower():
        return existing_display_name.strip()
    if external_identifier:
        pretty_identifier = " ".join(
            part.title() for part in external_identifier.replace("_", "-").split("-") if part
        )
        return f"{generic_label} / {pretty_identifier}"
    return generic_label


def _load_backfill_rows(bind: sa.engine.Connection) -> list[dict[str, object]]:
    source_rows = list(bind.execute(sa.text("SELECT * FROM job_sources")).mappings())
    job_rows = list(
        bind.execute(
            sa.text(
                """
                SELECT job_source_id, company, updated_at, posted_at, raw_payload
                FROM jobs
                """
            )
        ).mappings()
    )
    jobs_by_source: dict[str, list[dict[str, object]]] = defaultdict(list)
    for job in job_rows:
        jobs_by_source[str(job["job_source_id"])].append(dict(job))

    prepared_rows: list[dict[str, object]] = []
    for source in source_rows:
        source_dict = dict(source)
        jobs = jobs_by_source.get(str(source_dict["id"]), [])
        identifier = _infer_identifier(str(source_dict["slug"]), jobs)
        last_seen_at = max((job.get("updated_at") for job in jobs), default=None)

        prepared_rows.append(
            {
                "id": source_dict["id"],
                "slug": source_dict["slug"],
                "external_identifier": identifier,
                "display_name": _default_display_name(
                    str(source_dict["slug"]),
                    identifier,
                    str(source_dict["display_name"]),
                ),
                "base_url": _default_base_url(
                    str(source_dict["slug"]),
                    identifier,
                    source_dict.get("base_url"),
                ),
                "is_active": source_dict["is_active"],
                "last_sync_requested_at": None,
                "last_sync_started_at": last_seen_at,
                "last_sync_completed_at": last_seen_at,
                "last_successful_sync_at": last_seen_at,
                "last_error": None,
                "last_error_at": None,
                "last_fetched_job_count": len(jobs),
                "last_created_job_count": len(jobs),
                "last_updated_job_count": 0,
                "created_at": source_dict["created_at"],
                "updated_at": source_dict["updated_at"],
            }
        )

    return prepared_rows


def _rebuild_sqlite_job_sources(bind: sa.engine.Connection) -> None:
    rows = _load_backfill_rows(bind)

    op.execute(sa.text("PRAGMA foreign_keys=OFF"))
    job_sources_new = op.create_table(
        "job_sources__new",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column(
            "slug",
            sa.Enum(
                "greenhouse",
                "lever",
                "ashby",
                "manual",
                name="jobsource",
                native_enum=False,
            ),
            nullable=False,
        ),
        sa.Column("external_identifier", sa.String(length=255), nullable=True),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_sync_requested_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_sync_completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_fetched_job_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_created_job_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_updated_job_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "slug",
            "external_identifier",
            name="uq_job_sources_slug_external_identifier",
        ),
    )
    if rows:
        op.bulk_insert(job_sources_new, rows)

    op.drop_table("job_sources")
    op.rename_table("job_sources__new", "job_sources")
    op.create_index("ix_job_sources_slug", "job_sources", ["slug"], unique=False)
    op.execute(sa.text("PRAGMA foreign_keys=ON"))


def _alter_postgres_job_sources(bind: sa.engine.Connection) -> None:
    op.add_column(
        "job_sources",
        sa.Column("external_identifier", sa.String(length=255), nullable=True),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_sync_requested_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_sync_started_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_sync_completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_successful_sync_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("job_sources", sa.Column("last_error", sa.Text(), nullable=True))
    op.add_column(
        "job_sources",
        sa.Column("last_error_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_fetched_job_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_created_job_count", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "job_sources",
        sa.Column("last_updated_job_count", sa.Integer(), nullable=False, server_default="0"),
    )

    inspector = sa.inspect(bind)
    for constraint in inspector.get_unique_constraints("job_sources"):
        if constraint.get("column_names") == ["slug"] and constraint.get("name"):
            op.drop_constraint(constraint["name"], "job_sources", type_="unique")
            break

    op.drop_index("ix_job_sources_slug", table_name="job_sources")
    op.create_unique_constraint(
        "uq_job_sources_slug_external_identifier",
        "job_sources",
        ["slug", "external_identifier"],
    )
    op.create_index("ix_job_sources_slug", "job_sources", ["slug"], unique=False)

    rows = _load_backfill_rows(bind)
    for row in rows:
        bind.execute(
            sa.text(
                """
                UPDATE job_sources
                SET external_identifier = :external_identifier,
                    display_name = :display_name,
                    base_url = :base_url,
                    last_sync_requested_at = :last_sync_requested_at,
                    last_sync_started_at = :last_sync_started_at,
                    last_sync_completed_at = :last_sync_completed_at,
                    last_successful_sync_at = :last_successful_sync_at,
                    last_error = :last_error,
                    last_error_at = :last_error_at,
                    last_fetched_job_count = :last_fetched_job_count,
                    last_created_job_count = :last_created_job_count,
                    last_updated_job_count = :last_updated_job_count
                WHERE id = :id
                """
            ),
            row,
        )


def upgrade() -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        _rebuild_sqlite_job_sources(bind)
    else:
        _alter_postgres_job_sources(bind)


def downgrade() -> None:
    raise NotImplementedError("Downgrade is not supported for the multi-source registry migration.")
