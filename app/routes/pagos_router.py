from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.schemas.pagos import (
    MetodoPagoCreate, MetodoPagoOut,
    CuentaBancariaCreate, CuentaBancariaOut
)
from app.services.pagos_service import PagosService
from app.dependencies.auth_dependencies import require_pasajero, require_conductor

# Router para Pasajeros
router_pagos = APIRouter(prefix="/pagos", tags=["Pagos (Pasajero)"])
# Router para Conductores
router_cobros = APIRouter(prefix="/cobros", tags=["Cobros (Conductor)"])

# ================= RUTAS PASAJERO (TARJETAS) =================
@router_pagos.post("/tarjetas", response_model=MetodoPagoOut, status_code=201)
def agregar_tarjeta(data: MetodoPagoCreate, db: Session = Depends(get_db), user=Depends(require_pasajero)):
    return PagosService.crear_metodo_pago(db, user["id_usuario"], data)

@router_pagos.get("/tarjetas", response_model=List[MetodoPagoOut])
def listar_tarjetas(db: Session = Depends(get_db), user=Depends(require_pasajero)):
    return PagosService.listar_metodos_pago(db, user["id_usuario"])

@router_pagos.delete("/tarjetas/{id_metodo}", status_code=200)
def eliminar_tarjeta(id_metodo: str, db: Session = Depends(get_db), user=Depends(require_pasajero)):
    return PagosService.deshabilitar_metodo_pago(db, user["id_usuario"], id_metodo)

# ================= RUTAS CONDUCTOR (CUENTAS) =================
@router_cobros.post("/cuentas", response_model=CuentaBancariaOut, status_code=201)
def agregar_cuenta(data: CuentaBancariaCreate, db: Session = Depends(get_db), user=Depends(require_conductor)):
    return PagosService.crear_cuenta_bancaria(db, user["id_usuario"], data)

@router_cobros.get("/cuentas", response_model=List[CuentaBancariaOut])
def listar_cuentas(db: Session = Depends(get_db), user=Depends(require_conductor)):
    return PagosService.listar_cuentas_bancarias(db, user["id_usuario"])