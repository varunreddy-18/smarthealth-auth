from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import secrets
import uuid

from app.database.database import get_db

from app.schemas.user_schema import UserRegister
from app.schemas.auth_schema import LoginRequest, TokenResponse

from app.services.auth_service import register_user, authenticate_user
from app.services.session_service import create_session, store_refresh_token, get_session_by_refresh_id

from app.core.jwt import create_access_token
from app.core.security import hash_password, verify_password

from app.oauth.google import oauth
from app.models.user import User
from app.models.session import Session as UserSession

from app.core.limiter import limiter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ---------------- REGISTER ---------------- #

from fastapi import Request as FastAPIRequest


@router.post("/register")
@limiter.limit("10/minute")
def register(
    request: FastAPIRequest,
    user: UserRegister,
    db: Session = Depends(get_db)
):
    new_user = register_user(user, db)

    if not new_user:
        raise HTTPException(
            status_code=400,
            detail="Email already registered"
        )

    return {
        "message": "User registered successfully",
        "email": new_user.email
    }


# ---------------- LOGIN ---------------- #

@router.post("/login", response_model=TokenResponse)
@limiter.limit("5/minute")
def login(
    request: Request,
    login_data: LoginRequest,
    db: Session = Depends(get_db)
):

    user = authenticate_user(
        login_data.email,
        login_data.password,
        db
    )

    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )

    browser = request.headers.get("User-Agent", "Unknown Browser")
    ip_address = request.client.host
    device = "Desktop"

    # Create session first
    session = create_session(
        db=db,
        user_id=user.id,
        browser=browser,
        device=device,
        ip_address=ip_address
    )

    # Generate refresh token (id.selector format)
    token_id = uuid.uuid4().hex
    secret = secrets.token_urlsafe(48)
    refresh_token = f"{token_id}.{secret}"

    # Hash only the secret for storage
    secret_hash = hash_password(secret)
    refresh_expires = datetime.utcnow() + timedelta(days=30)

    # Store refresh token info in session (rotation-friendly)
    store_refresh_token(db, session.id, token_id, secret_hash, refresh_expires)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


# ---------------- GOOGLE LOGIN ---------------- #

@router.get("/google/login")
@limiter.limit("10/minute")
async def google_login(request: Request):
    redirect_uri = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(
        request,
        redirect_uri
    )


@router.get("/google/callback", name="google_callback")
async def google_callback(
    request: Request,
    db: Session = Depends(get_db)
):
    token = await oauth.google.authorize_access_token(request)

    user_info = token["userinfo"]

    email = user_info["email"]
    name = user_info["name"]

    user = db.query(User).filter(User.email == email).first()

    if not user:

        user = User(
            full_name=name,
            email=email,
            hashed_password="GOOGLE_LOGIN",
            role="patient",
            is_verified=True
        )

        db.add(user)
        db.commit()
        db.refresh(user)

    browser = request.headers.get("User-Agent", "Unknown Browser")
    ip_address = request.client.host
    device = "Desktop"

    session = create_session(
        db=db,
        user_id=user.id,
        browser=browser,
        device=device,
        ip_address=ip_address
    )

    # Generate refresh token for Google-login session as well
    token_id = uuid.uuid4().hex
    secret = secrets.token_urlsafe(48)
    refresh_token = f"{token_id}.{secret}"

    secret_hash = hash_password(secret)
    refresh_expires = datetime.utcnow() + timedelta(days=30)

    store_refresh_token(db, session.id, token_id, secret_hash, refresh_expires)

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token
    }


# ---------------- REFRESH ---------------- #

from pydantic import BaseModel


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/refresh", response_model=TokenResponse)
def refresh_token(request: RefreshRequest, db: Session = Depends(get_db)):
    # Expect format token_id.secret
    try:
        token_id, secret = request.refresh_token.split(".", 1)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    session = get_session_by_refresh_id(db, token_id)

    if not session or not session.is_active or not session.refresh_token_hash:
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Check expiry
    if session.refresh_token_expires and session.refresh_token_expires < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token expired")

    # Verify secret against stored hash
    if not verify_password(secret, session.refresh_token_hash):
        # Potential reuse or tampering — revoke session
        session.is_active = False
        db.add(session)
        db.commit()
        raise HTTPException(status_code=401, detail="Invalid refresh token")

    # Rotation: generate new token and replace stored values
    new_token_id = uuid.uuid4().hex
    new_secret = secrets.token_urlsafe(48)
    new_refresh_token = f"{new_token_id}.{new_secret}"

    new_secret_hash = hash_password(new_secret)
    new_expires = datetime.utcnow() + timedelta(days=30)

    store_refresh_token(db, session.id, new_token_id, new_secret_hash, new_expires)

    # Create new access token for user
    user = session.user

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": new_refresh_token
    }


# ---------------- LOGOUT ---------------- #

from app.dependencies.auth import get_current_user


@router.post("/logout")
def logout(request: Request, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    ip_address = request.client.host
    browser = request.headers.get("User-Agent", "Unknown Browser")

    # Find the most recent active session for this user matching IP/browser
    # Mark all active sessions for this user as inactive — ensure refresh tokens are revoked
    user_sessions = db.query(UserSession).filter(UserSession.user_id == current_user.id, UserSession.is_active == True).all()

    for s in user_sessions:
        s.is_active = False
        s.logout_time = datetime.utcnow()
        s.refresh_token_id = None
        s.refresh_token_hash = None
        s.refresh_token_expires = None
        db.add(s)

    db.commit()

    return {"message": "Logged out"}