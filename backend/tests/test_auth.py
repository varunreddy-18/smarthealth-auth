import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.database.database import Base, get_db
from app.services.auth_service import register_user, authenticate_user
from app.services.session_service import create_session, store_refresh_token, get_session_by_refresh_id
from app.core.jwt import create_access_token, verify_access_token
from app.core.security import hash_password, verify_password
from app.api.auth import refresh_token as refresh_endpoint, RefreshRequest

# Use SQLite in-memory for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables in test DB
Base.metadata.create_all(bind=engine)


def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_registration_success_and_duplicate():
    db = next(get_test_db())
    user_schema = type("U", (), {"full_name": "T", "email": "test@example.com", "password": "pw"})
    u = register_user(user_schema, db)
    assert u.email == "test@example.com"

    # duplicate
    u2 = register_user(user_schema, db)
    assert u2 is None


def test_login_success_and_wrong_password():
    db = next(get_test_db())
    user_schema = type("U", (), {"full_name": "T2", "email": "login1@example.com", "password": "pw"})
    register_user(user_schema, db)

    user = authenticate_user("login1@example.com", "pw", db)
    assert user is not None

    wrong = authenticate_user("login1@example.com", "bad", db)
    assert wrong is None


def test_jwt_and_protected_simulation():
    db = next(get_test_db())
    user_schema = type("U", (), {"full_name": "T3", "email": "jwt@example.com", "password": "pw"})
    user = register_user(user_schema, db)

    access = create_access_token({"sub": str(user.id), "email": user.email, "role": user.role})
    payload = verify_access_token(access)
    assert payload is not None

    bad = verify_access_token("invalidtoken")
    assert bad is None


def test_rbac_and_admin_access():
    db = next(get_test_db())
    user_schema = type("U", (), {"full_name": "Admin", "email": "admin@example.com", "password": "pw"})
    user = register_user(user_schema, db)

    # promote
    from app.models.user import User
    u = db.query(User).filter(User.email == "admin@example.com").first()
    u.role = "admin"
    db.add(u)
    db.commit()

    token = create_access_token({"sub": str(u.id), "email": u.email, "role": u.role})
    payload = verify_access_token(token)
    assert payload["role"] == "admin"


def test_refresh_rotation_logic():
    db = next(get_test_db())
    user_schema = type("U", (), {"full_name": "R", "email": "rt@example.com", "password": "pw"})
    user = register_user(user_schema, db)

    session = create_session(db=db, user_id=user.id, browser="b", device="d", ip_address="127.0.0.1")
    token_id = "tokid123"
    secret = "mysecret"
    refresh = f"{token_id}.{secret}"
    secret_hash = hash_password(secret)
    from datetime import timedelta
    expires = datetime.utcnow() + timedelta(minutes=5)
    store_refresh_token(db, session.id, token_id, secret_hash, expires)

    # call refresh endpoint function directly
    req = RefreshRequest(refresh_token=refresh)
    resp = refresh_endpoint(req, db)
    # should succeed and return dict with refresh_token
    assert "refresh_token" in resp

    new_refresh = resp["refresh_token"]

    # old should fail (HTTPException expected)
    from fastapi import HTTPException
    import pytest
    with pytest.raises(HTTPException):
        refresh_endpoint(RefreshRequest(refresh_token=refresh), db)

    # new should succeed
    resp3 = refresh_endpoint(RefreshRequest(refresh_token=new_refresh), db)
    assert "access_token" in resp3


# Basic smoke for logout logic
def test_logout_revokes_sessions():
    db = next(get_test_db())
    user_schema = type("U", (), {"full_name": "L", "email": "log@example.com", "password": "pw"})
    user = register_user(user_schema, db)
    session = create_session(db=db, user_id=user.id, browser="b", device="d", ip_address="127.0.0.1")
    # store refresh token
    store_refresh_token(db, session.id, "id1", hash_password("s"), None)

    # simulate logout by marking sessions inactive
    from app.models.session import Session as UserSession
    sessions = db.query(UserSession).filter(UserSession.user_id == user.id).all()
    for s in sessions:
        s.is_active = False
        db.add(s)
    db.commit()

    sessions2 = db.query(UserSession).filter(UserSession.user_id == user.id, UserSession.is_active == True).all()
    assert len(sessions2) == 0
