from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from uuid import UUID

class ValidacionUsuarioCreate(BaseModel):
    ine_frente: str
    ine_reverso: str
    licencia_frente: Optional[str] = None
    licencia_reverso: Optional[str] = None
    poliza: Optional[str] = None

class ValidacionUsuarioResponse(BaseModel):
    id_validacion: UUID
    id_usuario: UUID
    estado_validacion: Optional[str] = None
    motivo_rechazo: Optional[str] = None
    fecha_revision: Optional[datetime] = None
    ine_frente: str
    ine_reverso: str
    licencia_frente: Optional[str] = None
    licencia_reverso: Optional[str] = None
    poliza: Optional[str] = None

    class Config:
        from_attributes = True

class UsuarioResumen(BaseModel):
    id_usuario: UUID
    nombre: str  # Asumo que tienes un campo nombre en tu modelo de Usuario
    rol: str

    class Config:
        from_attributes = True

class ValidacionPendienteItem(BaseModel):
    validacion: ValidacionUsuarioResponse
    usuario: UsuarioResumen

class ValidacionesPendientesResponse(BaseModel):
    pasajeros: list[ValidacionPendienteItem]
    conductores: list[ValidacionPendienteItem]

class RechazoValidacionRequest(BaseModel):
    motivo_rechazo: str