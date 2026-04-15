from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.repositories import JobFocusRepository
from job_focus_shared import (
    ProfileUpdateDTO,
    ResumeDTO,
    UserPreferenceDTO,
    UserPreferenceUpdateDTO,
    UserProfileDTO,
)

router = APIRouter(prefix="/api/profile", tags=["profile"])


@router.get("/me", response_model=UserProfileDTO)
def get_profile(session: Session = Depends(get_db_session)) -> UserProfileDTO:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        raise HTTPException(status_code=404, detail="No user profile found.")
    return repository.to_user_profile_dto(user)


@router.put("/me", response_model=UserProfileDTO)
def update_profile(
    payload: ProfileUpdateDTO, session: Session = Depends(get_db_session)
) -> UserProfileDTO:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None or user.profile is None:
        raise HTTPException(status_code=404, detail="No user profile found.")
    return repository.to_user_profile_dto(repository.update_profile(user.profile, payload))


@router.get("/me/resume", response_model=ResumeDTO)
def get_resume(session: Session = Depends(get_db_session)) -> ResumeDTO:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        raise HTTPException(status_code=404, detail="No user profile found.")

    resume = repository.get_default_resume_for_user(user.id)
    if resume is None:
        raise HTTPException(status_code=404, detail="No resume found.")
    return repository.to_resume_dto(resume)


@router.get("/me/preferences", response_model=UserPreferenceDTO)
def get_preferences(session: Session = Depends(get_db_session)) -> UserPreferenceDTO:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        raise HTTPException(status_code=404, detail="No user profile found.")

    preferences = repository.get_or_create_user_preferences(user)
    return repository.to_user_preference_dto(preferences)


@router.put("/me/preferences", response_model=UserPreferenceDTO)
def update_preferences(
    payload: UserPreferenceUpdateDTO, session: Session = Depends(get_db_session)
) -> UserPreferenceDTO:
    repository = JobFocusRepository(session)
    user = repository.get_primary_user()
    if user is None:
        raise HTTPException(status_code=404, detail="No user profile found.")

    preferences = repository.get_or_create_user_preferences(user)
    return repository.to_user_preference_dto(repository.update_user_preferences(preferences, payload))
