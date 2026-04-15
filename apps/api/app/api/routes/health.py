from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db_session
from app.services.tracker import read_tracker_state

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check(session: Session = Depends(get_db_session)) -> dict[str, str]:
    database_status = "ok"
    try:
        session.execute(text("SELECT 1"))
    except Exception:
        database_status = "error"

    tracker_state = read_tracker_state()
    redis_status = "ok" if tracker_state["redis_connected"] else "unavailable"
    status = "ok" if database_status == "ok" else "degraded"

    return {"status": status, "database": database_status, "redis": redis_status}
