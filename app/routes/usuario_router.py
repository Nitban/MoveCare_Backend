from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import UUID

from app.core.database import get_db
from app.services.usuario_service import UsuarioService
from app.schemas.usuario import ConductorIdResponse

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"]
)


@router.get(
    "/{id_usuario}/conductor",
    response_model=ConductorIdResponse
)
def obtener_id_conductor(id_usuario: UUID, db: Session = Depends(get_db)):
    id_conductor = UsuarioService.obtener_id_conductor_por_usuario(
        db, id_usuario
    )

    if not id_conductor:
        raise HTTPException(
            status_code=404,
            detail="Conductor no encontrado para este usuario"
        )

    return {"id_conductor": id_conductor}
