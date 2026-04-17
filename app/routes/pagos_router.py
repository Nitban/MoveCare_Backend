import stripe
from fastapi import APIRouter, Depends, Request, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
# 🔥 Asumo que tienes tu config.py así, si no ajusta la ruta
from app.core.config import settings

from app.schemas.pagos import (
    MetodoPagoCreate, MetodoPagoOut,
    CuentaBancariaCreate, CuentaBancariaOut
)
from app.services.pagos_service import PagosService
from app.dependencies.auth_dependencies import require_pasajero, require_conductor

# Inicializar Stripe con tu llave secreta del .env
stripe.api_key = settings.STRIPE_SECRET_KEY

# Router para Pasajeros
router_pagos = APIRouter(prefix="/pagos", tags=["Pagos (Pasajero)"])
# Router para Conductores
router_cobros = APIRouter(prefix="/cobros", tags=["Cobros (Conductor)"])


# ================= ESQUEMAS PARA STRIPE =================
class PagoIntentRequest(BaseModel):
    monto: float  # El monto a cobrar
    id_viaje: str  # Para saber qué estamos cobrando


# ================= RUTAS STRIPE (NUEVAS) =================

@router_pagos.post("/crear-intencion", status_code=200)
def crear_intencion_pago(data: PagoIntentRequest, db: Session = Depends(get_db), user=Depends(require_pasajero)):
    """
    Paso 1: El frontend pide permiso para cobrar.
    Devuelve el client_secret que Flutter necesita para levantar el Payment Sheet.
    """
    try:
        # 🚨 REGLA DE ORO STRIPE: Los montos siempre van en la unidad más pequeña (centavos).
        # Si el viaje cuesta $150.50 MXN, debes enviar 15050.
        monto_centavos = int(data.monto * 100)

        # Creamos la intención de cobro en Stripe
        intent = stripe.PaymentIntent.create(
            amount=monto_centavos,
            currency="mxn",  # Cambia esto si usas otra moneda
            metadata={
                # Guardamos esta metadata para que el Webhook sepa a qué viaje corresponde este pago
                "id_viaje": data.id_viaje,
                "id_pasajero": user["id_usuario"]
            }
        )

        # Le regresamos al frontend (Flutter) la llave temporal para completar el pago
        return {"client_secret": intent.client_secret}

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router_pagos.post("/webhook", include_in_schema=False)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Paso 2: Stripe nos avisa asíncronamente si el cobro fue exitoso.
    OJO: Esta ruta es async porque necesitamos leer el request.body() puro.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    # Necesitas crear esta variable en tu .env. Stripe te la da en el dashboard (sección Webhooks)
    endpoint_secret = settings.STRIPE_WEBHOOK_SECRET

    try:
        # Verificamos matemáticamente que este aviso realmente venga de Stripe
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Payload inválido
        raise HTTPException(status_code=400)
    except stripe.error.SignatureVerificationError as e:
        # Firma inválida (alguien está intentando hackear tu endpoint)
        raise HTTPException(status_code=400)

    # Si la firma es correcta, revisamos qué pasó
    if event['type'] == 'payment_intent.succeeded':
        payment_intent = event['data']['object']

        # Extraemos la metadata que guardamos en /crear-intencion
        id_viaje = payment_intent.get("metadata", {}).get("id_viaje")

        # 🔥 AQUÍ LLAMAS A TU SERVICIO PARA MARCAR EL VIAJE COMO PAGADO 🔥
        # Ejemplo: PagosService.marcar_viaje_pagado(db, id_viaje)
        print(f"¡Éxito! El viaje {id_viaje} ha sido pagado.")

    elif event['type'] == 'payment_intent.payment_failed':
        print("El cobro falló. El usuario no tenía fondos o declinaron la tarjeta.")
        # Aquí podrías notificar al conductor/pasajero del fallo.

    # Siempre debes regresarle un 200 a Stripe para que sepa que recibiste el mensaje
    return {"status": "success"}


# ================= RUTAS PASAJERO (TARJETAS ACTUALES) =================
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