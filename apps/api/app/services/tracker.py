from __future__ import annotations

from datetime import datetime

from redis import Redis
from redis.exceptions import RedisError
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.repositories import JobFocusRepository
from app.models import Application, Job, JobMatch, User
from job_focus_shared import SourceHealthDTO, TrackerOverviewDTO

TRACKER_KEYS = {
    "last_ingest_at": "job_focus:worker:last_run:ingest",
    "last_score_at": "job_focus:worker:last_run:score",
    "last_packet_at": "job_focus:worker:last_run:packet",
    "last_apply_at": "job_focus:worker:last_run:apply",
}


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def read_tracker_state() -> dict[str, datetime | bool | None]:
    settings = get_settings()
    try:
        client = Redis.from_url(settings.redis_url, decode_responses=True)
        client.ping()
        return {
            "redis_connected": True,
            "last_ingest_at": _parse_datetime(client.get(TRACKER_KEYS["last_ingest_at"])),
            "last_score_at": _parse_datetime(client.get(TRACKER_KEYS["last_score_at"])),
            "last_packet_at": _parse_datetime(client.get(TRACKER_KEYS["last_packet_at"])),
            "last_apply_at": _parse_datetime(client.get(TRACKER_KEYS["last_apply_at"])),
        }
    except RedisError:
        return {
            "redis_connected": False,
            "last_ingest_at": None,
            "last_score_at": None,
            "last_packet_at": None,
            "last_apply_at": None,
        }
def build_tracker_overview(session: Session) -> TrackerOverviewDTO:
    repository = JobFocusRepository(session)
    counts = {
        "user_count": session.scalar(select(func.count(User.id))) or 0,
        "job_count": session.scalar(select(func.count(Job.id))) or 0,
        "match_count": session.scalar(select(func.count(JobMatch.id))) or 0,
        "application_count": session.scalar(select(func.count(Application.id))) or 0,
    }
    state = read_tracker_state()

    return TrackerOverviewDTO(
        **counts,
        configured_live_source_count=repository.count_configured_live_sources(),
        last_ingest_at=state["last_ingest_at"],
        last_score_at=state["last_score_at"],
        last_packet_at=state["last_packet_at"],
        last_apply_at=state["last_apply_at"],
        redis_connected=bool(state["redis_connected"]),
    )


def build_source_health(session: Session) -> list[SourceHealthDTO]:
    tracker_state = read_tracker_state()
    repository = JobFocusRepository(session)
    return repository.list_source_health(last_ingest_at=tracker_state["last_ingest_at"])
