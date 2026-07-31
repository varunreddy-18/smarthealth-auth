from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role

router = APIRouter(
    prefix="/doctor",
    tags=["Doctor"]
)


@router.get("/dashboard")
def doctor_dashboard(
    current_user=Depends(require_role(["doctor"]))
):
    return {
        "message": f"Welcome Dr. {current_user.full_name}"
    }