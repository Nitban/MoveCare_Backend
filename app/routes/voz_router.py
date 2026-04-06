"""
Router de Control por Voz — MoveCare

Endpoints:
  POST /ia/voz/interpretar  → Interpreta texto transcrito y devuelve intención + entidades
  POST /ia/voz/demo         → Demo pública sin autenticación (para pruebas)
"""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.ai.voz.voz_service import interpretar_comando
from app.dependencies.auth_dependencies import require_pasajero

router = APIRouter(prefix="/ia/voz", tags=["Voz"])


# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────

class ComandoVozPayload(BaseModel):
    texto: str = Field(
        ...,
        min_length=2,
        max_length=500,
        description="Texto transcrito del comando de voz del pasajero",
        example="Quiero un viaje al hospital central mañana a las 10",
    )


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post(
    "/interpretar",
    summary="Interpretar comando de voz del pasajero",
)
def interpretar_voz(
    payload: ComandoVozPayload,
    user=Depends(require_pasajero),
):
    """
    Recibe el texto transcrito del comando de voz del pasajero
    y devuelve la intención detectada, entidades extraídas y la
    acción que debe ejecutar la app Flutter.

    **Flujo recomendado en Flutter:**
    1. Activar micrófono con `speech_to_text`
    2. Enviar texto transcrito a este endpoint
    3. Leer `respuesta_voz` en voz alta (text_to_speech)
    4. Navegar a `accion.pantalla` con `accion.datos_prellenados`

    **Intenciones soportadas:**
    - `solicitar_viaje` → navegar a crear_viaje con datos prellenados
    - `solicitar_viaje_multiple` → viaje con múltiples paradas
    - `cancelar_viaje` → cancelar viaje activo
    - `ver_viaje_actual` → estado del viaje en curso
    - `ver_historial` → historial de viajes
    - `crear_acompanante` → registrar nuevo acompañante
    - `ver_acompanantes` → listar acompañantes
    - `ver_pagos` → métodos de pago
    - `ver_home` → pantalla de inicio
    - `no_reconocido` → comando no entendido
    """
    try:
        resultado = interpretar_comando(payload.texto)
        return {"ok": True, **resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al interpretar comando: {str(e)}")


@router.post(
    "/demo",
    summary="[DEMO] Interpretar comando de voz sin autenticación",
)
def demo_voz(payload: ComandoVozPayload):
    """
    **Endpoint público** para probar el módulo de voz sin autenticación.

    Ejemplos de comandos para probar:
    - `"Quiero un viaje"`
    - `"Ver mi historial de viajes"`
    - `"Agregar acompañante"`
    - `"Quiero ir primero a la farmacia, luego al hospital y después al mercado"`
    - `"Cancela mi viaje"`
    - `"Mis métodos de pago"`
    """
    try:
        resultado = interpretar_comando(payload.texto)
        return {
            "ok": True,
            "nota": "Demo sin autenticación — solo para desarrollo/presentación",
            **resultado,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al interpretar comando: {str(e)}")
