from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories import (
    DuplicateApplicationError,
    InvalidApplicationTransitionError,
    JobFocusRepository,
)
from job_focus_shared import ApplicationDTO, ApplicationReviewRequestDTO, ApplicationStatus, ReviewAction

router = APIRouter(prefix="/api/applications", tags=["applications"])


@router.get("", response_model=list[ApplicationDTO])
def get_applications(session: Session = Depends(get_db_session)) -> list[ApplicationDTO]:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        return []
    return [repository.to_application_dto(item) for item in repository.list_applications_for_user(user.id)]


@router.post("/{job_id}/apply", response_model=ApplicationDTO, status_code=status.HTTP_201_CREATED)
def apply_to_job(job_id: str, session: Session = Depends(get_db_session)) -> ApplicationDTO:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        raise HTTPException(status_code=404, detail="No user profile found.")

    job = repository.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found.")

    try:
        application = repository.create_application(
            user=user,
            job=job,
            notes="Created from the applications API.",
        )
    except DuplicateApplicationError as error:
        application = error.application

    return repository.to_application_dto(application)


@router.post("/{application_id}/review", response_model=ApplicationDTO)
def review_application(
    application_id: str,
    payload: ApplicationReviewRequestDTO,
    session: Session = Depends(get_db_session),
) -> ApplicationDTO:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        raise HTTPException(status_code=404, detail="No user profile found.")

    application = repository.get_application_for_user(user.id, application_id)
    if application is None:
        raise HTTPException(status_code=404, detail="Application not found.")

    action_note = payload.note or (
        "Manually approved from dashboard."
        if payload.action == ReviewAction.APPROVE
        else "Manually rejected from dashboard."
    )

    try:
        if payload.action == ReviewAction.APPROVE:
            if application.status != ApplicationStatus.WAITING_REVIEW:
                raise HTTPException(
                    status_code=409,
                    detail="Only waiting_review applications can be approved.",
                )
            repository.record_application_event(
                application=application,
                event_type="manual_review_approved",
                actor="dashboard",
                note=action_note,
                payload={},
                commit=False,
            )
            application = repository.transition_application_status(
                application,
                ApplicationStatus.SUBMITTING,
                actor="dashboard",
                note=action_note,
                current_packet=application.current_packet,
            )
        else:
            repository.record_application_event(
                application=application,
                event_type="manual_review_rejected",
                actor="dashboard",
                note=action_note,
                payload={},
                commit=False,
            )
            application = repository.transition_application_status(
                application,
                ApplicationStatus.BLOCKED,
                actor="dashboard",
                note=action_note,
                blocking_reason=action_note,
                current_packet=application.current_packet,
            )
    except InvalidApplicationTransitionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error

    refreshed = repository.get_application_for_user(user.id, application.id)
    if refreshed is None:
        raise HTTPException(status_code=404, detail="Application not found after update.")
    return repository.to_application_dto(refreshed)
