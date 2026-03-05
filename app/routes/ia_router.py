"""
Router de Inteligencia Artificial – MoveCare

Endpoints:
  POST /ia/conductores/ubicacion        → Conductor actualiza su posición GPS
  GET  /ia/conductores/disponibles      → Admin: lista conductores sin viaje activo
  POST /ia/viajes/asignar               → Admin: asigna conductores a TODOS los viajes pendientes
  POST /ia/viajes/{id_viaje}/asignar    → Admin: asigna conductor a un viaje específico
"""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.ai.asignacion.asignacion_service import (
    _conductores_disponibles,
    actualizar_ubicacion,
    asignar_conductores,
)
from app.core.database import get_db
from app.dependencies.auth_dependencies import require_admin, require_conductor
from app.models.conductor_model import Conductor

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])


# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────

class UbicacionPayload(BaseModel):
    latitud: float = Field(..., ge=-90, le=90, description="Latitud WGS-84")
    longitud: float = Field(..., ge=-180, le=180, description="Longitud WGS-84")


class AsignarViajesPayload(BaseModel):
    ids_viaje: list[str] | None = Field(
        default=None,
        description="UUIDs de viajes a procesar. Omitir para procesar todos los pendientes.",
    )


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post("/conductores/ubicacion", summary="Actualizar ubicación del conductor")
def actualizar_ubicacion_conductor(
    payload: UbicacionPayload,
    db: Session = Depends(get_db),
    user=Depends(require_conductor),
):
    """
    El conductor envía sus coordenadas GPS actuales.
    Se usa para calcular la distancia en la asignación de viajes.
    Debe llamarse cada vez que la app del conductor actualice la posición.
    """
    conductor = (
        db.query(Conductor)
        .filter(Conductor.id_usuario == user["id_usuario"])
        .first()
    )
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    actualizar_ubicacion(
        db=db,
        id_conductor=conductor.id_conductor,
        latitud=payload.latitud,
        longitud=payload.longitud,
    )

    return {"ok": True, "mensaje": "Ubicación actualizada"}


@router.get("/conductores/disponibles", summary="Listar conductores disponibles")
def listar_conductores_disponibles(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Devuelve todos los conductores activos que no tienen un viaje en curso o agendado.
    Incluye su última ubicación conocida y rating promedio.
    """
    conductores = _conductores_disponibles(db)
    return {"total": len(conductores), "conductores": conductores}


@router.post("/viajes/asignar", summary="Asignar conductores a viajes pendientes")
def asignar_viajes(
    payload: AsignarViajesPayload = AsignarViajesPayload(),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Ejecuta el algoritmo húngaro para asignar el conductor óptimo
    a cada viaje en estado Pendiente.

    - Si se proporcionan `ids_viaje`, solo procesa esos viajes.
    - Si se omite, procesa todos los viajes Pendiente sin conductor.

    El conductor asignado se selecciona según:
      1. Compatibilidad de accesibilidad (40%)
      2. Proximidad al punto de inicio (35%)
      3. Calificación promedio (15%)
      4. Capacidad para acompañantes (10%)
    """
    try:
        resultado = asignar_conductores(db=db, ids_viaje=payload.ids_viaje)
        return {"ok": True, **resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en asignación: {str(e)}")


@router.post("/viajes/{id_viaje}/asignar", summary="Asignar conductor a un viaje específico")
def asignar_viaje_especifico(
    id_viaje: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Variante que asigna el conductor óptimo a un único viaje.
    Útil para reasignaciones o cuando se crea un viaje urgente.
    """
    try:
        resultado = asignar_conductores(db=db, ids_viaje=[id_viaje])
        if resultado["asignados"] == 0:
            raise HTTPException(
                status_code=422,
                detail=resultado.get("mensaje", "No se pudo asignar conductor"),
            )
        return {"ok": True, **resultado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en asignación: {str(e)}")
