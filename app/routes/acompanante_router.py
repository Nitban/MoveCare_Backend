from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.acompanante import (
    AcompananteCreate,
    AcompananteOut
)
from app.services.acompanante_service import AcompananteService
from app.dependencies.auth_dependencies import require_pasajero


router = APIRouter(prefix="/acompanantes", tags=["Acompañantes"])


# ================= CREAR =================
@router.post(
    "",
    response_model=AcompananteOut,
    status_code=201
)
def crear_acompanante(
    data: AcompananteCreate,
    db: Session = Depends(get_db),
    user=Depends(require_pasajero) # Aquí ya validas que sea pasajero
):
    # Usamos el ID que viene del token (seguridad garantizada)
    return AcompananteService.crear(
        db=db,
        id_usuario=user["id_usuario"],
        data=data
    )

# ================= LISTAR =================
@router.get(
    "",
    response_model=List[AcompananteOut]
)
def listar_acompanantes(
    db: Session = Depends(get_db),
    user=Depends(require_pasajero)
):
    return AcompananteService.listar_por_usuario(
        db=db,
        id_usuario=user["id_usuario"]
    )
