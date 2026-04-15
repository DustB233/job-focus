from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories import JobFocusRepository
from job_focus_shared import AuthSessionDTO, LoginRequestDTO

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=AuthSessionDTO)
def login(payload: LoginRequestDTO, session: Session = Depends(get_db_session)) -> AuthSessionDTO:
    repository = JobFocusRepository(session)
    user = repository.get_user_by_email(payload.email) or repository.get_primary_user()
    if user is None or payload.password != user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid demo credentials.",
        )

    return repository.to_auth_session_dto(token=f"demo-token-{user.id[:8]}", user=user)
