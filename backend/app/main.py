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
app = FastAPI(
    title="SmartHealth Auth API",
    version="1.0.0"
)

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
