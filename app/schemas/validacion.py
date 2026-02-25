from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

# Lo que recibimos del Frontend (Base64 o URLs, dependiendo de cómo subas la imagen)
class ValidacionUsuarioCreate(BaseModel):
    ine_frente: str
    ine_reverso: str

# Lo que devolvemos al Frontend
class ValidacionUsuarioResponse(BaseModel):
    id_validacion: UUID
    id_usuario: UUID
    estado_validacion: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    fecha_revision: Optional[datetime] = None
    ine_frente: str
    ine_reverso: str

    class Config:
        from_attributes = True