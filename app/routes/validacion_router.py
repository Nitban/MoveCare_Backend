from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.services.validacion_service import ValidacionService
from app.schemas.validacion import ValidacionesPendientesResponse, ValidacionUsuarioResponse, RechazoValidacionRequest
from uuid import UUID

# Importa tu función de seguridad actual
from app.core.security import get_current_user

router = APIRouter(
    prefix="/validaciones",
    tags=["Validaciones"]
)

@router.get("/pendientes", response_model=ValidacionesPendientesResponse)
def listar_validaciones_pendientes(
    db: Session = Depends(get_db)
):
    return ValidacionService.obtener_validaciones_pendientes(db)

@router.put("/{id_validacion}/aceptar", response_model=ValidacionUsuarioResponse)
def aceptar_validacion(
    id_validacion: UUID,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user) # <-- 1. Sabemos que es un diccionario
):
    # 2. Sacamos el ID usando la clave del diccionario
    # (Si tu token guarda el id con otro nombre, como "sub" o "id", cámbialo aquí)
    admin_id = str(current_admin.get("id_usuario"))

    return ValidacionService.aceptar_validacion(db, str(id_validacion), admin_id)

@router.put("/{id_validacion}/rechazar", response_model=ValidacionUsuarioResponse)
def rechazar_validacion(
    id_validacion: UUID,
    datos: RechazoValidacionRequest,
    db: Session = Depends(get_db),
    current_admin: dict = Depends(get_current_user) # <-- 1. Sabemos que es un diccionario
):
    # 2. Sacamos el ID usando la clave del diccionario
    admin_id = str(current_admin.get("id_usuario"))

    return ValidacionService.rechazar_validacion(db, str(id_validacion), datos.motivo_rechazo, admin_id)