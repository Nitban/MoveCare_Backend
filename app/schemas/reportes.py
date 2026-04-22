from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class ReporteCreate(BaseModel):
    id_reportante: UUID
    id_reportado: UUID
    tipo_reporte: str
    descripcion: str
    id_viaje: UUID

class ReporteUpdateEstado(BaseModel):
    estado: str  # "Aceptado" o "Rechazado"
    motivo_rechazo: str

class ReporteResponse(BaseModel):
    id_reporte: UUID
    id_reportante: UUID
    id_reportado: UUID
    tipo_reporte: str
    descripcion: str
    estado: str
    id_viaje: Optional[UUID] = None

    class Config:
        from_attributes = True