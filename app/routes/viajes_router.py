from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependencies import require_pasajero
from app.schemas.viaje import CrearViajeSchema
from app.services.viaje_service import ViajeService

router = APIRouter(prefix="/viajes", tags=["Viajes"])


@router.post("/crear")
def crear_viaje(
    data: CrearViajeSchema,
    db: Session = Depends(get_db),
    user=Depends(require_pasajero)
):
    try:
        viaje = ViajeService.crear_viaje(
            db=db,
            id_usuario=user["id_usuario"],
            data=data
        )

        return {
            "ok": True,
            "mensaje": "Viaje creado correctamente",
            "viaje_id": viaje.id_viaje
        }

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
