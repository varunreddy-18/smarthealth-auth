from sqlalchemy.orm import Session as DBSession

from app.models.session import Session


def create_session(
    db: DBSession,
    user_id: int,
    browser: str,
    device: str,
    ip_address: str,
    refresh_token_id: str = None,
    refresh_token_hash: str = None,
    refresh_token_expires = None
):
    session = Session(
        user_id=user_id,
        browser=browser,
        device=device,
        ip_address=ip_address,
        is_active=True,
        refresh_token_id=refresh_token_id,
        refresh_token_hash=refresh_token_hash,
        refresh_token_expires=refresh_token_expires
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def store_refresh_token(db: DBSession, session_id: int, token_id: str, token_hash: str, expires):
    session = db.query(Session).filter(Session.id == session_id).first()

    if not session:
        return None

    session.refresh_token_id = token_id
    session.refresh_token_hash = token_hash
    session.refresh_token_expires = expires

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def get_session_by_refresh_id(db: DBSession, token_id: str):
    return db.query(Session).filter(Session.refresh_token_id == token_id).first()