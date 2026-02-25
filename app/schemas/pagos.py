from uuid import UUID
from typing import Optional
from pydantic import BaseModel, Field

# ================= METODO PAGO (PASAJERO) =================
class MetodoPagoBase(BaseModel):
    alias: Optional[str] = None
    token_tarjeta: str
    ultimos_cuatro: str = Field(..., min_length=4, max_length=4)
    marca: Optional[str] = None

class MetodoPagoCreate(MetodoPagoBase):
    pass # No necesitamos más campos al crear

class MetodoPagoOut(MetodoPagoBase):
    id_metodo: UUID
    id_pasajero: UUID
    activo: bool

    class Config:
        from_attributes = True

# ================= CUENTA BANCARIA (CONDUCTOR) =================
class CuentaBancariaBase(BaseModel):
    banco: str
    token_cuenta: str
    titular: str
    ultimos_cuatro: str = Field(..., min_length=4, max_length=4)

class CuentaBancariaCreate(CuentaBancariaBase):
    pass

class CuentaBancariaOut(CuentaBancariaBase):
    id_cuenta: UUID
    id_conductor: UUID

    class Config:
        from_attributes = True