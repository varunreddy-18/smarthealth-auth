from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database.database import get_db

from app.schemas.user_schema import UserRegister
from app.schemas.auth_schema import LoginRequest, TokenResponse

from app.services.auth_service import register_user, authenticate_user
from app.services.session_service import create_session

from app.core.jwt import create_access_token

from app.oauth.google import oauth
from app.models.user import User

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)


# ---------------- REGISTER ---------------- #

@router.post("/register")
def register(
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

    create_session(
        db=db,
        user_id=user.id,
        browser=browser,
        device=device,
        ip_address=ip_address
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


# ---------------- GOOGLE LOGIN ---------------- #

@router.get("/google/login")
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

    create_session(
        db=db,
        user_id=user.id,
        browser=browser,
        device=device,
        ip_address=ip_address
    )

    access_token = create_access_token(
        {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role
        }
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }