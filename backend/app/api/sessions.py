from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database.database import get_db
from app.dependencies.auth import get_current_user
from app.models.user import User
from app.models.session import Session as UserSession

router = APIRouter(
    prefix="/sessions",
    tags=["Sessions"]
)


@router.get("/me")
def my_sessions(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):

    sessions = (
        db.query(UserSession)
        .filter(UserSession.user_id == current_user.id)
        .order_by(UserSession.login_time.desc())
        .all()
    )

    return sessions