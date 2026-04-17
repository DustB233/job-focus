from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories import AUTOMATED_SOURCE_SLUGS, JobFocusRepository
from app.services.tracker import read_tracker_state
from job_focus_shared import SourceCreateDTO, SourceRegistryDTO

router = APIRouter(prefix="/api/sources", tags=["sources"])


def _last_ingest_at() -> datetime | None:
    tracker_state = read_tracker_state()
    value = tracker_state["last_ingest_at"]
    return value if isinstance(value, datetime) else None


@router.get("", response_model=list[SourceRegistryDTO])
def list_sources(session: Session = Depends(get_db_session)) -> list[SourceRegistryDTO]:
    repository = JobFocusRepository(session)
    return repository.list_source_registry_dtos(last_ingest_at=_last_ingest_at())


@router.post("", response_model=SourceRegistryDTO, status_code=status.HTTP_201_CREATED)
def create_source(
    payload: SourceCreateDTO,
    session: Session = Depends(get_db_session),
) -> SourceRegistryDTO:
    if payload.source not in AUTOMATED_SOURCE_SLUGS:
        raise HTTPException(
            status_code=422,
            detail=(
                "Only Greenhouse and Lever sources can be registered for automated ingest. "
                "LinkedIn and Handshake remain manual-only."
            ),
        )

    repository = JobFocusRepository(session)
    source = repository.create_job_source(payload)
    return repository.to_source_registry_dto(source, last_ingest_at=_last_ingest_at())


@router.post("/{source_id}/enable", response_model=SourceRegistryDTO)
def enable_source(source_id: str, session: Session = Depends(get_db_session)) -> SourceRegistryDTO:
    repository = JobFocusRepository(session)
    source = repository.get_job_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    source = repository.set_job_source_active(source, True)
    return repository.to_source_registry_dto(source, last_ingest_at=_last_ingest_at())


@router.post("/{source_id}/disable", response_model=SourceRegistryDTO)
def disable_source(source_id: str, session: Session = Depends(get_db_session)) -> SourceRegistryDTO:
    repository = JobFocusRepository(session)
    source = repository.get_job_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")

    source = repository.set_job_source_active(source, False)
    return repository.to_source_registry_dto(source, last_ingest_at=_last_ingest_at())


@router.post("/{source_id}/sync", response_model=SourceRegistryDTO)
def sync_source(source_id: str, session: Session = Depends(get_db_session)) -> SourceRegistryDTO:
    repository = JobFocusRepository(session)
    source = repository.get_job_source(source_id)
    if source is None:
        raise HTTPException(status_code=404, detail="Source not found.")
    if source.slug not in AUTOMATED_SOURCE_SLUGS:
        raise HTTPException(
            status_code=409,
            detail="This provider does not support automated ingest.",
        )
    if not source.external_identifier:
        raise HTTPException(
            status_code=409,
            detail="Source is missing its external identifier and cannot be synced.",
        )

    source = repository.mark_job_source_sync_requested(
        source,
        requested_at=datetime.now(timezone.utc),
    )
    return repository.to_source_registry_dto(source, last_ingest_at=_last_ingest_at())
