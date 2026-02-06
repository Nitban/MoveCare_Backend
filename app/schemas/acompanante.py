from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class AcompananteBase(BaseModel):
    nombre_completo: str
    parentesco: Optional[str] = None
    ine_frente: Optional[str] = None
    ine_reverso: Optional[str] = None

class AcompananteCreate(AcompananteBase):
    id_usuario: Optional[UUID] = None

class AcompananteOut(AcompananteBase):
    id_acompanante: UUID
    id_pasajero: UUID

    class Config:
        from_attributes = True