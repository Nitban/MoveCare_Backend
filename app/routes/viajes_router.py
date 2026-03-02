from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependencies import require_pasajero, require_conductor
from app.schemas.viaje import CrearViajeSchema, ViajeDetalleResponse
from app.services.viaje_service import ViajeService
from typing import List

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

@router.get("/historial", response_model=List[ViajeDetalleResponse])
def obtener_historial(
    db: Session = Depends(get_db),
    user = Depends(require_pasajero)
):
    try:
        historial = ViajeService.obtener_historial_pasajero(
            db=db,
            id_usuario=user["id_usuario"]
        )
        return historial
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/historial-conductor")
def obtener_historial_conductor(
    db: Session = Depends(get_db),
    user = Depends(require_conductor) # 🔥 Solo conductores pueden ver esto
):
    try:
        historial = ViajeService.obtener_historial_conductor(
            db=db,
            id_usuario=user["id_usuario"]
        )
        return historial
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.put("/{id_viaje}/cancelar")
def cancelar_viaje(
    id_viaje: str,
    db: Session = Depends(get_db),
    user=Depends(require_pasajero)
):
    try:
        ViajeService.cancelar_viaje(
            db=db,
            id_viaje=id_viaje,
            id_usuario=user["id_usuario"]
        )

        return {
            "ok": True,
            "mensaje": "Viaje cancelado exitosamente"
        }

    except ValueError as e:
        # Si el viaje no existe o ya estaba cancelado, arrojamos un error 400
        raise HTTPException(status_code=400, detail=str(e))