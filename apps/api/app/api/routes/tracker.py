from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.tracker import build_source_health, build_tracker_overview
from job_focus_shared import SourceHealthDTO, TrackerOverviewDTO

router = APIRouter(prefix="/api/tracker", tags=["tracker"])


@router.get("/overview", response_model=TrackerOverviewDTO)
def get_tracker_overview(session: Session = Depends(get_db_session)) -> TrackerOverviewDTO:
    return build_tracker_overview(session)


@router.get("/sources", response_model=list[SourceHealthDTO])
def get_source_health(session: Session = Depends(get_db_session)) -> list[SourceHealthDTO]:
    return build_source_health(session)
