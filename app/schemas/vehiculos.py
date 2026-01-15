from pydantic import BaseModel
from typing import Optional
from uuid import UUID

class VehiculoBase(BaseModel):
    marca: Optional[str] = None
    modelo: Optional[str] = None
    placas: Optional[str] = None
    color: Optional[str] = None
    capacidad: Optional[int] = None
    accesorios: Optional[str] = None


class VehiculoCreate(VehiculoBase):
    id_conductor: UUID


class VehiculoResponse(VehiculoBase):
    id_vehiculo: UUID
    id_conductor: UUID

    class Config:
        from_attributes = True

