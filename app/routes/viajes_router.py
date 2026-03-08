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


@router.get("/conductor/usuario/{id_usuario}/viajes/{estado}")
def obtener_viajes_conductor(id_usuario: str, estado: str, db: Session = Depends(get_db)):

    valid_estados = ['Pendiente', 'Agendado']
    if estado not in valid_estados:
        raise HTTPException(
            status_code=400,
            detail="Estado no válido. Usa 'Pendiente' o 'Agendado'."
        )

    try:
        viajes = ViajeService.obtener_viajes_por_estado_conductor(db, id_usuario, estado)
        return {"status": "success", "data": viajes}
    except ValueError as ve:
        # Para manejar si no encontramos al conductor
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


#Especificamente para el conductor
@router.put("/{id_viaje}/aceptar")
def aceptar_viaje(id_viaje: str, db: Session = Depends(get_db)):
    try:
        ViajeService.aceptar_viaje(db, id_viaje)
        return {"status": "success", "message": "Viaje aceptado y agendado."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/{id_viaje}/rechazar")
def rechazar_viaje(id_viaje: str, db: Session = Depends(get_db)):
    try:
        ViajeService.liberar_viaje(db, id_viaje)
        return {"status": "success", "message": "Viaje rechazado exitosamente."}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/viaje_actual/{id_viaje}")
def obtener_viaje_actual(id_viaje: str, db: Session = Depends(get_db)):
    try:
        # Aquí asumo que crearás este método en tu ViajeService
        viaje = ViajeService.obtener_viaje_por_id(db, id_viaje)
        if not viaje:
            raise HTTPException(status_code=404, detail="Viaje no encontrado")
        return viaje
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))