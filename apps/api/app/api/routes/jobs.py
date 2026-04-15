from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories import JobFocusRepository
from job_focus_shared import JobDTO

router = APIRouter(prefix="/api/jobs", tags=["jobs"])


@router.get("", response_model=list[JobDTO])
def get_jobs(session: Session = Depends(get_db_session)) -> list[JobDTO]:
    repository = JobFocusRepository(session)
    return [repository.to_job_dto(job) for job in repository.list_jobs()]
