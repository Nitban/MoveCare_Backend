"""
Router de Control por Voz — MoveCare

Endpoints:
  POST /ia/voz/interpretar       → Interpreta texto transcrito y devuelve intención + entidades
  POST /ia/voz/interpretar-audio → Transcribe audio con Whisper e interpreta intención
  POST /ia/voz/demo              → Demo pública sin autenticación (para pruebas)
"""

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel, Field
from openai import OpenAI

from app.ai.voz.voz_service import interpretar_comando
from app.dependencies.auth_dependencies import require_pasajero
from app.core.config import settings

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
    "/interpretar-audio",
    summary="Transcribir audio con Whisper e interpretar intención",
)
async def interpretar_audio(
    audio: UploadFile = File(...),
    user=Depends(require_pasajero),
):
    """
    Recibe un archivo de audio (M4A, WEBM, WAV, MP3),
    lo transcribe con Whisper y devuelve intención + entidades.
    """
    if not settings.OPENAI_API_KEY:
        raise HTTPException(status_code=503, detail="OPENAI_API_KEY no configurada")
    try:
        client = OpenAI(api_key=settings.OPENAI_API_KEY)
        audio_bytes = await audio.read()
        transcripcion = client.audio.transcriptions.create(
            model="whisper-1",
            file=(audio.filename or "audio.webm", audio_bytes, audio.content_type or "audio/webm"),
            language="es",
        )
        texto = transcripcion.text.strip()
        resultado = interpretar_comando(texto)
        return {"ok": True, **resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al procesar audio: {str(e)}")


@router.post(
    "/demo",
    summary="[DEMO] Interpretar comando de voz sin autenticación",
)
def demo_voz(payload: ComandoVozPayload):
    """
    **Endpoint público** para probar el módulo de voz sin autenticación.

    Ejemplos de comandos para probar:
    - `"Quiero un viaje al hospital mañana a las 10"`
    - `"Ver mi historial de viajes"`
    - `"Agregar acompañante, se llama María García, es mi hija"`
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
