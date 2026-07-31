from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role

router = APIRouter(
    prefix="/patient",
    tags=["Patient"]
)


@router.get("/dashboard")
def patient_dashboard(
    current_user=Depends(require_role(["patient"]))
):
    return {
        "message": f"Welcome Patient {current_user.full_name}"
    }