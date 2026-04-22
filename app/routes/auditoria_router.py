from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
# Ajusta esta ruta a donde tengas tu dependencia de seguridad/token
from app.dependencies.auth_dependencies import require_admin

from app.schemas.auditoria import AuditoriaResponse
from app.services.auditoria_service import AuditoriaService

router = APIRouter(
    prefix="/auditoria",
    tags=["Auditorias"]
)

@router.get("/", response_model=List[AuditoriaResponse])
def obtener_auditorias(
    db: Session = Depends(get_db),
    admin = Depends(require_admin) # Protegemos la ruta para que solo entre el admin
):
    try:
        auditorias = AuditoriaService.get_historial_auditorias(db)
        return auditorias
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))