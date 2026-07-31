from sqlalchemy.orm import Session as DBSession

from app.models.session import Session


def create_session(
    db: DBSession,
    user_id: int,
    browser: str,
    device: str,
    ip_address: str
):
    session = Session(
        user_id=user_id,
        browser=browser,
        device=device,
        ip_address=ip_address,
        is_active=True
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session