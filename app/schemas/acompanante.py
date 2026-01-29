from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class AcompananteBase(BaseModel):
    nombre_completo: str
    foto: Optional[str] = None
    telefono: Optional[str] = None
    parentesco: Optional[str] = None


class AcompananteCreate(AcompananteBase):
    id_usuario: UUID  # lo mandan desde el frontend


class AcompananteOut(BaseModel):
    id_acompanante: UUID
    nombre_completo: str
    foto: Optional[str] = None
    parentesco: Optional[str] = None

    class Config:
        from_attributes = True
