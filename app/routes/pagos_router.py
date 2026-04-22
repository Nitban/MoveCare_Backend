import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.config import settings
from app.schemas.pagos import (
    MetodoPagoCreate, MetodoPagoOut,
    CuentaBancariaCreate, CuentaBancariaOut,
    PagoIntentRequest, CobroTokenRequest
)
from app.services.pagos_service import PagosService
from app.dependencies.auth_dependencies import require_pasajero, require_conductor

stripe.api_key = settings.STRIPE_SECRET_KEY

router_pagos = APIRouter(prefix="/pagos", tags=["Pagos (Pasajero)"])
router_cobros = APIRouter(prefix="/cobros", tags=["Cobros (Conductor)"])

# ================= RUTAS STRIPE =================

@router_pagos.post("/crear-intencion", status_code=200)
def crear_intencion_pago(data: PagoIntentRequest, db: Session = Depends(get_db), user=Depends(require_pasajero)):
    """Paso 1: Para pagos nuevos (Payment Sheet en Flutter)."""
    try:
        intent = stripe.PaymentIntent.create(
            amount=int(data.monto * 100),
            currency="mxn",
            metadata={"id_viaje": data.id_viaje, "id_pasajero": user["id_usuario"]}
        )
        return {"client_secret": intent.client_secret}
    except Exception as e:
        raise HTTPException(400, detail=str(e))

@router_pagos.post("/cobrar-con-token", status_code=200)
def cobrar_con_token(data: CobroTokenRequest, db: Session = Depends(get_db), user=Depends(require_pasajero)):
    """Paso 1 alternativo: Cobrar usando una tarjeta ya registrada."""
    return PagosService.cobrar_con_tarjeta_guardada(db, user["id_usuario"], data)

@router_pagos.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except:
        raise HTTPException(400)

    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']
        id_viaje = payment_intent.get("metadata", {}).get("id_viaje")
        PagosService.marcar_viaje_pagado(db, id_viaje)

    elif event['type'] == 'payment_intent.payment_failed':
        payment_intent = event['data']['object']
        id_viaje = payment_intent.get("metadata", {}).get("id_viaje")
        PagosService.marcar_viaje_fallido(db, id_viaje)

    return {"status": "success"}

# ================= RUTAS CRUD TARJETAS =================
@router_pagos.post("/tarjetas", response_model=MetodoPagoOut, status_code=201)
def agregar_tarjeta(data: MetodoPagoCreate, db: Session = Depends(get_db), user=Depends(require_pasajero)):
    return PagosService.crear_metodo_pago(db, user["id_usuario"], data)

@router_pagos.get("/tarjetas", response_model=List[MetodoPagoOut])
def listar_tarjetas(db: Session = Depends(get_db), user=Depends(require_pasajero)):
    return PagosService.listar_metodos_pago(db, user["id_usuario"])

@router_pagos.delete("/tarjetas/{id_metodo}")
def eliminar_tarjeta(id_metodo: str, db: Session = Depends(get_db), user=Depends(require_pasajero)):
    return PagosService.deshabilitar_metodo_pago(db, user["id_usuario"], id_metodo)

# ================= RUTAS CONDUCTOR =================
@router_cobros.post("/cuentas", response_model=CuentaBancariaOut, status_code=201)
def agregar_cuenta(data: CuentaBancariaCreate, db: Session = Depends(get_db), user=Depends(require_conductor)):
    return PagosService.crear_cuenta_bancaria(db, user["id_usuario"], data)

@router_cobros.get("/cuentas", response_model=List[CuentaBancariaOut])
def listar_cuentas(db: Session = Depends(get_db), user=Depends(require_conductor)):
    return PagosService.listar_cuentas_bancarias(db, user["id_usuario"])