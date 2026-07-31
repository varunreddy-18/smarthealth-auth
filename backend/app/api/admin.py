from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role

router = APIRouter(
    prefix="/admin",
    tags=["Admin"]
)


@router.get("/dashboard")
def admin_dashboard(
    current_user=Depends(require_role(["admin"]))
):
    return {
        "message": f"Welcome Admin {current_user.full_name}"
    }