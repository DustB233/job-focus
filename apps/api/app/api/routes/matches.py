from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories import JobFocusRepository
from job_focus_shared import MatchDTO

router = APIRouter(prefix="/api/matches", tags=["matches"])


@router.get("", response_model=list[MatchDTO])
def get_matches(session: Session = Depends(get_db_session)) -> list[MatchDTO]:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        return []
    return [repository.to_match_dto(match) for match in repository.list_matches_for_user(user.id)]
