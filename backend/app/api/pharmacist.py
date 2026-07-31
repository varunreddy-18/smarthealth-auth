from fastapi import APIRouter, Depends

from app.dependencies.auth import require_role

router = APIRouter(
    prefix="/pharmacist",
    tags=["Pharmacist"]
)


@router.get("/dashboard")
def pharmacist_dashboard(
    current_user=Depends(require_role(["pharmacist"]))
):
    return {
        "message": f"Welcome Pharmacist {current_user.full_name}"
    }