"""Create normalized job focus schema.

Revision ID: 20260412_0001
Revises:
Create Date: 2026-04-12 23:59:00
"""

from alembic import op
import sqlalchemy as sa


revision = "20260412_0001"
down_revision = None
branch_labels = None
depends_on = None


application_status = sa.Enum(
    "discovered",
    "shortlisted",
    "draft_ready",
    "needs_user_input",
    "waiting_review",
    "submitting",
    "submitted",
    "failed",
    "blocked",
    "duplicate",
    name="applicationstatus",
    native_enum=False,
)
employment_type = sa.Enum(
    "full_time",
    "contract",
    "internship",
    name="employmenttype",
    native_enum=False,
)
job_source = sa.Enum(
    "greenhouse",
    "lever",
    "ashby",
    "manual",
    name="jobsource",
    native_enum=False,
)
match_strength = sa.Enum("high", "medium", "low", name="matchstrength", native_enum=False)
packet_status = sa.Enum(
    "draft_ready",
    "needs_user_input",
    "waiting_review",
    "finalized",
    name="packetstatus",
    native_enum=False,
)
work_mode = sa.Enum("remote", "hybrid", "onsite", name="workmode", native_enum=False)


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("hashed_password", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)

    op.create_table(
        "job_sources",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("slug", job_source, nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("base_url", sa.String(length=512), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("slug"),
    )
    op.create_index(op.f("ix_job_sources_slug"), "job_sources", ["slug"], unique=True)

    op.create_table(
        "profiles",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("target_roles", sa.JSON(), nullable=False),
        sa.Column("years_experience", sa.Integer(), nullable=False),
        sa.Column("seniority_level", sa.String(length=64), nullable=True),
        sa.Column("authorization_regions", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(op.f("ix_profiles_user_id"), "profiles", ["user_id"], unique=True)

    op.create_table(
        "resumes",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("skills", sa.JSON(), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "version", name="uq_resumes_user_version"),
    )
    op.create_index(op.f("ix_resumes_user_id"), "resumes", ["user_id"], unique=False)

    op.create_table(
        "jobs",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("job_source_id", sa.String(length=36), nullable=False),
        sa.Column("external_job_id", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("location", sa.String(length=255), nullable=False),
        sa.Column("work_mode", work_mode, nullable=False),
        sa.Column("employment_type", employment_type, nullable=False),
        sa.Column("salary_min", sa.Integer(), nullable=False),
        sa.Column("salary_max", sa.Integer(), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("application_url", sa.String(length=1024), nullable=True),
        sa.Column("seniority_level", sa.String(length=64), nullable=True),
        sa.Column("authorization_requirement", sa.String(length=255), nullable=True),
        sa.Column("raw_payload", sa.JSON(), nullable=False),
        sa.Column("normalized_payload", sa.JSON(), nullable=False),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_source_id"], ["job_sources.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_source_id", "external_job_id", name="uq_jobs_source_external_id"),
    )
    op.create_index(op.f("ix_jobs_job_source_id"), "jobs", ["job_source_id"], unique=False)

    op.create_table(
        "job_matches",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("match_score", sa.Integer(), nullable=False),
        sa.Column("strength", match_strength, nullable=False),
        sa.Column("rationale", sa.Text(), nullable=False),
        sa.Column("why_matched", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_job_matches_user_job"),
    )
    op.create_index(op.f("ix_job_matches_job_id"), "job_matches", ["job_id"], unique=False)
    op.create_index(op.f("ix_job_matches_user_id"), "job_matches", ["user_id"], unique=False)

    op.create_table(
        "application_packets",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("resume_id", sa.String(length=36), nullable=True),
        sa.Column("status", packet_status, nullable=False),
        sa.Column("selected_resume_version", sa.Integer(), nullable=True),
        sa.Column("tailored_resume_summary", sa.Text(), nullable=True),
        sa.Column("cover_note", sa.Text(), nullable=True),
        sa.Column("screening_answers", sa.JSON(), nullable=False),
        sa.Column("missing_fields", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["resume_id"], ["resumes.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_packets_job_id"), "application_packets", ["job_id"], unique=False
    )
    op.create_index(
        op.f("ix_application_packets_user_id"), "application_packets", ["user_id"], unique=False
    )

    op.create_table(
        "applications",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("job_id", sa.String(length=36), nullable=False),
        sa.Column("current_packet_id", sa.String(length=36), nullable=True),
        sa.Column("status", application_status, nullable=False),
        sa.Column("notes", sa.Text(), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("blocking_reason", sa.Text(), nullable=True),
        sa.Column("duplicate_of_application_id", sa.String(length=36), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["current_packet_id"], ["application_packets.id"]),
        sa.ForeignKeyConstraint(["duplicate_of_application_id"], ["applications.id"]),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "job_id", name="uq_applications_user_job"),
    )
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"], unique=False)
    op.create_index(op.f("ix_applications_user_id"), "applications", ["user_id"], unique=False)

    op.create_table(
        "application_events",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("application_id", sa.String(length=36), nullable=False),
        sa.Column("from_status", application_status, nullable=True),
        sa.Column("to_status", application_status, nullable=False),
        sa.Column("event_type", sa.String(length=64), nullable=False),
        sa.Column("actor", sa.String(length=64), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_application_events_application_id"),
        "application_events",
        ["application_id"],
        unique=False,
    )

    op.create_table(
        "auth_sessions",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("token_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_auth_sessions_token_hash"), "auth_sessions", ["token_hash"], unique=True
    )
    op.create_index(op.f("ix_auth_sessions_user_id"), "auth_sessions", ["user_id"], unique=False)

    op.create_table(
        "user_preferences",
        sa.Column("id", sa.String(length=36), nullable=False),
        sa.Column("user_id", sa.String(length=36), nullable=False),
        sa.Column("preferred_locations", sa.JSON(), nullable=False),
        sa.Column("preferred_work_modes", sa.JSON(), nullable=False),
        sa.Column("preferred_employment_types", sa.JSON(), nullable=False),
        sa.Column("desired_salary_min", sa.Integer(), nullable=True),
        sa.Column("desired_salary_max", sa.Integer(), nullable=True),
        sa.Column("auto_apply_enabled", sa.Boolean(), nullable=False),
        sa.Column("auto_apply_min_score", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index(
        op.f("ix_user_preferences_user_id"), "user_preferences", ["user_id"], unique=True
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_user_preferences_user_id"), table_name="user_preferences")
    op.drop_table("user_preferences")
    op.drop_index(op.f("ix_auth_sessions_user_id"), table_name="auth_sessions")
    op.drop_index(op.f("ix_auth_sessions_token_hash"), table_name="auth_sessions")
    op.drop_table("auth_sessions")
    op.drop_index(op.f("ix_application_events_application_id"), table_name="application_events")
    op.drop_table("application_events")
    op.drop_index(op.f("ix_applications_user_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_job_id"), table_name="applications")
    op.drop_table("applications")
    op.drop_index(op.f("ix_application_packets_user_id"), table_name="application_packets")
    op.drop_index(op.f("ix_application_packets_job_id"), table_name="application_packets")
    op.drop_table("application_packets")
    op.drop_index(op.f("ix_job_matches_user_id"), table_name="job_matches")
    op.drop_index(op.f("ix_job_matches_job_id"), table_name="job_matches")
    op.drop_table("job_matches")
    op.drop_index(op.f("ix_jobs_job_source_id"), table_name="jobs")
    op.drop_table("jobs")
    op.drop_index(op.f("ix_resumes_user_id"), table_name="resumes")
    op.drop_table("resumes")
    op.drop_index(op.f("ix_profiles_user_id"), table_name="profiles")
    op.drop_table("profiles")
    op.drop_index(op.f("ix_job_sources_slug"), table_name="job_sources")
    op.drop_table("job_sources")
    op.drop_index(op.f("ix_users_email"), table_name="users")
    op.drop_table("users")

    packet_status.drop(op.get_bind(), checkfirst=False)
    match_strength.drop(op.get_bind(), checkfirst=False)
    work_mode.drop(op.get_bind(), checkfirst=False)
    job_source.drop(op.get_bind(), checkfirst=False)
    employment_type.drop(op.get_bind(), checkfirst=False)
    application_status.drop(op.get_bind(), checkfirst=False)
