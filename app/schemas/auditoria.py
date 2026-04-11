from pydantic import BaseModel
from typing import Optional
from uuid import UUID
from datetime import datetime

class AuditoriaResponse(BaseModel):
    id_auditoria: UUID
    id_admin: UUID
    nombre_admin: str # <-- ¡Nuevo!
    accion: str
    tabla_afectada: str
    id_objetivo: Optional[UUID] = None
    detalle: Optional[str] = None
    fecha: datetime
    ip_origen: Optional[str] = None
    estado_validacion: Optional[str] = None # <-- ¡Nuevo!
    motivo_rechazo: Optional[str] = None    # <-- ¡Nuevo!