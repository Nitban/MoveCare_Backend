from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependencies import require_pasajero, require_conductor
from app.services.app_service import AppService

router = APIRouter(
    prefix="/home",
    tags=["Home"]
)

# ================= HOME PASAJERO =================
@router.get("/home/pasajero")
def home_pasajero(
    db: Session = Depends(get_db),
    user=Depends(require_pasajero)
):
    return AppService.get_home_pasajero(
        db=db,
        id_usuario=user["id_usuario"]
    )

# ================= HOME CONDUCTOR =================
@router.get("/home/conductor")
def home_conductor(
    db: Session = Depends(get_db),
    user=Depends(require_conductor)
):
    return AppService.get_home_conductor(
        db=db,
        id_usuario=user["id_usuario"]
    )

