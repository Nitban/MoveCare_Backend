from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class NotificacionBase(BaseModel):
    titulo: str
    mensaje: str
    tipo: str

class NotificacionCreate(NotificacionBase):
    id_usuario: UUID

class NotificacionResponse(NotificacionBase):
    id_notificacion: UUID
    id_usuario: UUID
    leida: bool
    fecha_creacion: datetime

    class Config:
        from_attributes = True