from sqlalchemy.orm import Session

from app.models.user import User
from app.schemas.user_schema import UserRegister
from app.core.security import hash_password


def register_user(user: UserRegister, db: Session):

    existing_user = (
        db.query(User)
        .filter(User.email == user.email)
        .first()
    )

    if existing_user:
        return None

    new_user = User(
        full_name=user.full_name,
        email=user.email,
        hashed_password=hash_password(user.password),
        role="patient"
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
from app.core.security import verify_password


def authenticate_user(email: str, password: str, db: Session):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return None

    if not verify_password(password, user.hashed_password):
        return None

    return user