from fastapi import FastAPI

from app.api.auth import router as auth_router
from app.api.users import router as users_router
from starlette.middleware.sessions import SessionMiddleware
from app.core.config import settings
from app.database.database import Base, engine
from app.models.user import User
from app.models.session import Session
from fastapi.middleware.cors import CORSMiddleware
from app.api.admin import router as admin_router
from app.api.patient import router as patient_router
from app.api.doctor import router as doctor_router
from app.api.pharmacist import router as pharmacist_router
from app.api.sessions import router as session_router

# Rate limiter
from app.core.limiter import limiter
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi import _rate_limit_exceeded_handler

app = FastAPI(
    title="SmartHealth Auth API",
    version="1.0.0"
)

# Attach limiter to app state and middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)

app.include_router(users_router)
app.include_router(admin_router)
app.include_router(patient_router)
app.include_router(doctor_router)
app.include_router(pharmacist_router)
app.include_router(session_router)

import os
import sys

# Create tables only when not running under pytest to avoid touching prod DB during tests
# Detect pytest by checking sys.modules for 'pytest'
if "pytest" not in sys.modules and "PYTEST_CURRENT_TEST" not in os.environ:
    Base.metadata.create_all(bind=engine)


@app.get("/")
def root():
    return {
        "message": "SmartHealth Auth API Running"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }
