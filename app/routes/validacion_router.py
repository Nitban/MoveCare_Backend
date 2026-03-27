from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db # Importa tu dependencia de base de datos
from app.services.validacion_service import ValidacionService
from app.schemas.validacion import ValidacionesPendientesResponse, ValidacionUsuarioResponse, RechazoValidacionRequest
from uuid import UUID

router = APIRouter(
    prefix="/validaciones",
    tags=["Validaciones"]
)

@router.get("/pendientes", response_model=ValidacionesPendientesResponse)
def listar_validaciones_pendientes(db: Session = Depends(get_db)):

    return ValidacionService.obtener_validaciones_pendientes(db)

@router.put("/{id_validacion}/aceptar", response_model=ValidacionUsuarioResponse)
def aceptar_validacion(id_validacion: UUID, db: Session = Depends(get_db)):
    return ValidacionService.aceptar_validacion(db, str(id_validacion))

@router.put("/{id_validacion}/rechazar", response_model=ValidacionUsuarioResponse)
def rechazar_validacion(
    id_validacion: UUID,
    datos: RechazoValidacionRequest,
    db: Session = Depends(get_db)
):
    return ValidacionService.rechazar_validacion(db, str(id_validacion), datos.motivo_rechazo)