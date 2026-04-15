from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Application, Job, Resume, User
from app.repositories import DuplicateApplicationError, JobFocusRepository


def get_primary_user(session: Session) -> User | None:
    return JobFocusRepository(session).get_primary_user()


def get_user_by_email(session: Session, email: str) -> User | None:
    return JobFocusRepository(session).get_user_by_email(email)


def get_resume_for_user(session: Session, user_id: str) -> Resume | None:
    return JobFocusRepository(session).get_default_resume_for_user(user_id)


def list_jobs(session: Session) -> list[Job]:
    return JobFocusRepository(session).list_jobs()


def list_applications_for_user(session: Session, user_id: str) -> list[Application]:
    return JobFocusRepository(session).list_applications_for_user(user_id)


def get_job(session: Session, job_id: str) -> Job | None:
    return JobFocusRepository(session).get_job(job_id)


def create_application_for_job(session: Session, user: User, job: Job) -> Application:
    repository = JobFocusRepository(session)
    try:
        return repository.create_application(user=user, job=job)
    except DuplicateApplicationError as error:
        return error.application
