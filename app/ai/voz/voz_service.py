"""
Módulo de Control por Voz — MoveCare

Flujo:
  1. Flutter transcribe el audio en el dispositivo (speech_to_text, gratis/offline)
  2. Envía el texto al endpoint POST /ia/voz/interpretar
  3. Este servicio detecta la intención y extrae entidades
  4. Devuelve JSON estructurado que Flutter usa para navegar/ejecutar la acción

Intenciones soportadas:
  - solicitar_viaje         → crear un viaje simple
  - solicitar_viaje_multiple → viaje con múltiples paradas
  - ver_historial           → historial de viajes
  - cancelar_viaje          → cancelar viaje activo
  - ver_viaje_actual        → estado del viaje en curso
  - ver_acompanantes        → listar acompañantes
  - crear_acompanante       → registrar nuevo acompañante
  - ver_pagos               → listar métodos de pago
  - ver_home                → pantalla de inicio
  - no_reconocido           → el texto no coincide con ninguna intención

Sin dependencias externas — solo módulos built-in de Python (re, datetime).
Compatible con OpenAI Whisper cuando se agregue la API key.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta
from typing import Optional

try:
    from openai import OpenAI as _OpenAI
    from app.core.config import settings as _settings
    _openai_disponible = True
except ImportError:
    _openai_disponible = False


# ──────────────────────────────────────────────
# Patrones de intención (español, case-insensitive)
# ──────────────────────────────────────────────

_PATRONES_INTENCION = {
    "solicitar_viaje_multiple": [
        r"varias\s+paradas",
        r"m[uú]ltiples\s+destinos",
        r"primero\s+a.+luego",
        r"primero\s+a.+despu[eé]s",
        r"pasar\s+por.+y\s+(luego|despu[eé]s|tambi[eé]n)",
        r"ir\s+a.+y\s+(luego|despu[eé]s)\s+a",
    ],
    "solicitar_viaje": [
        r"quiero\s+un\s+viaje",
        r"pedir\s+un\s+viaje",
        r"necesito\s+un\s+viaje",
        r"ll[eé]vame\s+a",
        r"necesito\s+ir\s+a",
        r"quiero\s+ir\s+a",
        r"me\s+puedes\s+llevar",
        r"solicitar\s+viaje",
        r"pide\s+un\s+carro",
        r"pedir\s+carro",
        r"quiero\s+ir",
        r"agendar\s+(un\s+)?viaje",
        r"programar\s+(un\s+)?viaje",
        r"quiero\s+viajar",
        r"necesito\s+transporte",
        r"pide\s+(un\s+)?viaje",
        r"un\s+viaje",
        r"\bviaje\s+(?:al?|hasta|hacia)\s+",
        r"necesito\s+(un\s+)?carro",
        r"quiero\s+(un\s+)?carro",
        r"^viaje$",
        r"^agendar$",
    ],
    "cancelar_viaje": [
        r"cancela\s+(mi\s+)?viaje",
        r"cancelar\s+(mi\s+)?viaje",
        r"no\s+quiero\s+el\s+viaje",
        r"ya\s+no\s+quiero\s+el\s+viaje",
        r"cancela\s+mi\s+solicitud",
    ],
    "ver_viaje_actual": [
        r"c[oó]mo\s+va\s+mi\s+viaje",
        r"d[oó]nde\s+est[aá]\s+(el\s+)?conductor",
        r"estado\s+del\s+viaje",
        r"mi\s+viaje\s+actual",
        r"viaje\s+en\s+curso",
        r"cu[aá]nto\s+falta",
        r"ya\s+vienen",
    ],
    "ver_historial": [
        r"historial",
        r"mis\s+viajes\s+anteriores",
        r"viajes\s+pasados",
        r"ver\s+mis\s+viajes",
        r"viajes\s+que\s+he\s+hecho",
        r"viajes\s+realizados",
        r"mis\s+viajes",
        r"mi\s+historial",
        r"ver\s+historial",
        r"historial\s+de\s+viajes",
    ],
    "ver_perfil": [
        r"\bperfil\b",
        r"mi\s+perfil",
        r"ver\s+(mi\s+)?perfil",
        r"mis\s+datos",
        r"mi\s+cuenta",
        r"mi\s+informaci[oó]n",
        r"datos\s+personales",
    ],
    "crear_acompanante": [
        r"agregar\s+(un\s+)?acompa[nñ]ante",
        r"agrega\s+(un\s+)?acompa[nñ]ante",
        r"a[nñ]adir\s+(un\s+)?acompa[nñ]ante",
        r"nuevo\s+acompa[nñ]ante",
        r"registrar\s+(un\s+)?acompa[nñ]ante",
        r"registra\s+(un\s+)?acompa[nñ]ante",
        r"crear\s+(un\s+)?acompa[nñ]ante",
        r"crea\s+(un\s+)?acompa[nñ]ante",
        r"acompa[nñ]ante\b",
    ],
    "ver_acompanantes": [
        r"mis\s+acompa[nñ]antes",
        r"ver\s+acompa[nñ]antes",
        r"lista\s+de\s+acompa[nñ]antes",
        r"qu[eé]\s+acompa[nñ]antes\s+tengo",
        r"acompa[nñ]antes\s+registrados",
    ],
    "ver_pagos": [
        r"mis\s+tarjetas",
        r"m[eé]todos\s+de\s+pago",
        r"formas\s+de\s+pago",
        r"mis\s+pagos",
        r"ver\s+tarjetas",
        r"mis\s+m[eé]todos",
    ],
    "ver_home": [
        r"inicio",
        r"pantalla\s+principal",
        r"p[aá]gina\s+principal",
        r"home",
        r"men[uú]\s+principal",
        r"regresar\s+al\s+inicio",
        r"ir\s+al\s+inicio",
    ],
    # ── Confirmación / Cancelación de acción ──────────────────────────────
    "confirmar": [
        r"^s[ií]$",
        r"^ok$",
        r"^dale$",
        r"^listo$",
        r"^correcto$",
        r"s[ií]\s+confirmo",
        r"aceptar",
        r"confirmar",
        r"proceder",
        r"adelante",
        r"s[ií]\s+por\s+favor",
        r"s[ií]\s+quiero",
    ],
    "cancelar_accion": [
        r"^no$",
        r"^no\s+gracias$",
        r"cancelar\s+esto",
        r"cancelar\s+la\s+acci[oó]n",
        r"mejor\s+no",
        r"lo\s+dejo",
    ],
    # ── Navegación ────────────────────────────────────────────────────────
    "ir_atras": [
        r"regresar",
        r"volver",
        r"atr[aá]s",
        r"salir\s+de\s+aqu[ií]",
        r"salir\s+de\s+esta\s+pantalla",
        r"ir\s+atr[aá]s",
        r"volver\s+atr[aá]s",
        r"cerrar\s+esta\s+pantalla",
    ],
    # ── Historial ─────────────────────────────────────────────────────────
    "filtrar_completados": [
        r"(?:mostrar|ver|filtrar|solo)\s+(?:los\s+)?(?:viajes\s+)?completados",
        r"viajes\s+completados",
        r"(?:los\s+)?completados",
    ],
    "filtrar_cancelados": [
        r"(?:mostrar|ver|filtrar|solo)\s+(?:los\s+)?(?:viajes\s+)?cancelados",
        r"viajes\s+cancelados",
        r"(?:los\s+)?cancelados",
    ],
    "filtrar_todos": [
        r"(?:mostrar|ver)\s+todos",
        r"todos\s+los\s+viajes",
        r"quitar\s+filtro",
        r"sin\s+filtro",
        r"ver\s+todo",
    ],
    # ── Agendamiento ──────────────────────────────────────────────────────
    "establecer_origen": [
        r"(?:mi\s+)?origen\s+es",
        r"(?:mi\s+)?origen\s+\w",   # "origen Andares" sin "es"
        r"salgo\s+desde",
        r"saliendo\s+desde",
        r"vengo\s+de",
        r"estoy\s+en",
        r"me\s+encuentro\s+en",
    ],
    "establecer_hora": [
        r"\d{1,2}\s+de\s+la\s+(?:noche|tarde|ma[nñ]ana)",  # "9 de la noche"
        r"(?:son\s+)?las\s+\d{1,2}",                        # "las 9", "son las 9"
        r"hora\s+\d{1,2}",                                   # "hora 9"
        r"p[oó]nle\s+(?:la\s+hora\s+)?\d{1,2}",            # "ponle 9"
    ],
    "establecer_destino": [
        r"(?:el\s+)?destino\s+es",
        r"quiero\s+ir\s+a",
        r"ll[eé]vame\s+a",
        r"me\s+llevo\s+a",
        r"ir\s+(?:al?|hasta)\s+",
    ],
    "agregar_parada": [
        r"agregar\s+parada",
        r"a[nñ]adir\s+parada",
        r"agrega\s+(?:una\s+)?parada",
        r"parar\s+(?:también\s+)?en",
        r"tambi[eé]n\s+(?:ir\s+)?a",
        r"pasando\s+por",
    ],
    "quitar_parada": [
        r"quitar\s+(?:la\s+[uú]ltima\s+)?parada",
        r"eliminar\s+(?:la\s+[uú]ltima\s+)?parada",
        r"borrar\s+parada",
        r"[uú]ltima\s+parada\s+no",
        r"quita\s+(?:esa\s+)?parada",
    ],
    # ── Reporte ───────────────────────────────────────────────────────────
    "enviar_reporte": [
        r"enviar\s+reporte",
        r"mandar\s+reporte",
        r"confirmar\s+reporte",
        r"reportar\s+el\s+problema",
        r"enviar\s+incidencia",
        r"mandar\s+la\s+queja",
        r"enviar\s+la\s+queja",
    ],
}

# Días de la semana en español
_DIAS = {
    "lunes": 0, "martes": 1, "miércoles": 2, "miercoles": 2,
    "jueves": 3, "viernes": 4, "sábado": 5, "sabado": 5, "domingo": 6,
}

# Parentescos comunes
_PARENTESCOS = [
    "hijo", "hija", "esposo", "esposa", "padre", "madre", "hermano", "hermana",
    "abuelo", "abuela", "nieto", "nieta", "primo", "prima", "tío", "tia",
    "sobrino", "sobrina", "amigo", "amiga", "cuidador", "cuidadora",
]


# ──────────────────────────────────────────────
# Detección de intención
# ──────────────────────────────────────────────

_INTENCIONES_VALIDAS = list(_PATRONES_INTENCION.keys()) + ["no_reconocido"]

_SYSTEM_PROMPT = """Eres el asistente de voz de MoveCare, app de transporte para personas mayores o con necesidades especiales.

Detecta la intención del usuario y responde ÚNICAMENTE con el nombre exacto de la intención.

Intenciones disponibles:
- solicitar_viaje: quiere pedir un viaje, taxi o transporte
- solicitar_viaje_multiple: quiere un viaje con varias paradas
- cancelar_viaje: quiere cancelar un viaje
- ver_viaje_actual: pregunta por su viaje en curso
- ver_historial: quiere ver viajes anteriores
- ver_perfil: quiere ver su perfil o datos
- crear_acompanante: quiere agregar un acompañante
- ver_acompanantes: quiere ver sus acompañantes
- ver_pagos: quiere ver métodos de pago o tarjetas
- ver_home: quiere ir a la pantalla principal
- confirmar: confirma una acción ("sí", "dale", "ok")
- cancelar_accion: cancela una acción ("no", "mejor no")
- ir_atras: quiere regresar a la pantalla anterior
- filtrar_completados: filtrar viajes completados
- filtrar_cancelados: filtrar viajes cancelados
- filtrar_todos: ver todos los viajes
- establecer_origen: indica desde dónde sale
- establecer_hora: indica la hora del viaje ("9 de la noche", "las 3 de la tarde")
- establecer_destino: indica a dónde quiere ir
- agregar_parada: quiere agregar una parada al viaje
- quitar_parada: quiere eliminar una parada
- enviar_reporte: quiere enviar un reporte o queja
- no_reconocido: no corresponde a ninguna intención

Responde SOLO con el nombre de la intención, sin explicación."""


def _detectar_con_gpt(texto: str) -> tuple[str, float]:
    """Fallback: usa GPT-4o-mini cuando el regex no reconoce la intención."""
    if not _openai_disponible:
        return "no_reconocido", 0.0

    api_key = getattr(_settings, "OPENAI_API_KEY", "")
    if not api_key:
        return "no_reconocido", 0.0

    try:
        client = _OpenAI(api_key=api_key)
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": texto},
            ],
            max_tokens=20,
            temperature=0,
        )
        intencion = response.choices[0].message.content.strip().lower()
        if intencion not in _INTENCIONES_VALIDAS:
            return "no_reconocido", 0.0
        return intencion, 0.75
    except Exception:
        return "no_reconocido", 0.0


def detectar_intencion(texto: str) -> tuple[str, float]:
    """
    Detecta la intención del texto.
    Primero intenta regex (rápido, gratis).
    Si no reconoce nada, usa GPT-4o-mini como fallback.
    """
    texto_norm = texto.lower().strip()

    for intencion, patrones in _PATRONES_INTENCION.items():
        for patron in patrones:
            if re.search(patron, texto_norm):
                return intencion, 0.9

    return _detectar_con_gpt(texto)


# ──────────────────────────────────────────────
# Extracción de entidades
# ──────────────────────────────────────────────

def _extraer_destino(texto: str) -> Optional[str]:
    """Extrae el destino principal del texto."""
    patrones = [
        r"(?:ir|llevarme|llévame|voy|quiero\s+ir)\s+(?:al?|hasta|hacia)\s+([a-záéíóúüñ\d\s]+?)(?:\s+(?:mañana|hoy|el\b|a\s+las|desde)|,|$)",
        r"(?:viaje|carro)\s+(?:al?|hasta|hacia)\s+([a-záéíóúüñ\d\s]+?)(?:\s+(?:mañana|hoy|el\b|a\s+las|desde)|,|$)",
        r"(?:al?|hasta|hacia)\s+([a-záéíóúüñ\d\s]{3,40})(?:\s+(?:mañana|hoy|el\b|a\s+las|desde)|,|$)",
        r"destino\s+([a-záéíóúüñ\d\s]+?)(?:\s+(?:mañana|hoy|el\b|a\s+las)|,|$)",
    ]
    texto_norm = texto.lower()
    for patron in patrones:
        m = re.search(patron, texto_norm)
        if m:
            return m.group(1).strip().title()
    return None


def _extraer_origen(texto: str) -> Optional[str]:
    """Extrae el punto de inicio del texto."""
    patrones = [
        r"(?:desde|de|saliendo\s+de)\s+([a-záéíóúüñ\d\s]+?)(?:\s+(?:al?\b|hasta|hacia|a\s+las)|,|$)",
        r"(?:estoy|me\s+encuentro)\s+en\s+([a-záéíóúüñ\d\s]+?)(?:\s+(?:al?\b|hasta|hacia|a\s+las)|,|$)",
        r"(?:punto\s+de\s+inicio|origen)\s+(?:es\s+)?([a-záéíóúüñ\d\s]+?)(?:\s|,|$)",
    ]
    texto_norm = texto.lower()
    for patron in patrones:
        m = re.search(patron, texto_norm)
        if m:
            return m.group(1).strip().title()
    return None


def _extraer_hora_sola(texto: str) -> Optional[dict]:
    """
    Extrae hora y minutos de frases sin contexto de viaje completo.
    Ejemplos: '9 de la noche', 'las 3 de la tarde', 'son las 10'.
    Retorna dict con 'hora' y 'minutos' como strings de 2 dígitos, o None.
    """
    texto_norm = texto.lower()
    hora = None
    minutos = 0
    periodo = ""

    # Patrón 1: "X de la noche/tarde/mañana"
    m = re.search(r"(\d{1,2})(?::(\d{2}))?\s+de\s+la\s+(noche|tarde|ma[nñ]ana)", texto_norm)
    if m:
        hora = int(m.group(1))
        minutos = int(m.group(2)) if m.group(2) else 0
        periodo = m.group(3)

    # Patrón 2: "las X [de la noche/tarde]" o "son las X"
    if hora is None:
        m = re.search(r"(?:son\s+)?las\s+(\d{1,2})(?::(\d{2}))?\s*(?:de\s+la\s+(noche|tarde|ma[nñ]ana))?", texto_norm)
        if m:
            hora = int(m.group(1))
            minutos = int(m.group(2)) if m.group(2) else 0
            periodo = m.group(3) or ""

    # Patrón 3: "hora X"
    if hora is None:
        m = re.search(r"hora\s+(\d{1,2})(?::(\d{2}))?", texto_norm)
        if m:
            hora = int(m.group(1))
            minutos = int(m.group(2)) if m.group(2) else 0

    if hora is None:
        return None

    # Ajuste AM/PM
    if periodo in ("tarde", "noche") and hora < 12:
        hora += 12
    elif periodo == "mañana" and hora == 12:
        hora = 0

    return {"hora": f"{hora:02d}", "minutos": f"{minutos:02d}"}


def _extraer_fecha_hora(texto: str) -> Optional[str]:
    """
    Extrae y normaliza fecha/hora a formato ISO 8601.
    Soporta: hoy, mañana, días de la semana, horas en formato 12h/24h.
    """
    texto_norm = texto.lower()
    ahora = datetime.now()
    fecha_base = ahora.date()
    hora_base = None

    # Detectar día base
    if "mañana" in texto_norm:
        fecha_base = (ahora + timedelta(days=1)).date()
    elif "hoy" in texto_norm:
        fecha_base = ahora.date()
    else:
        for dia_nombre, dia_num in _DIAS.items():
            if dia_nombre in texto_norm:
                dias_hasta = (dia_num - ahora.weekday()) % 7
                if dias_hasta == 0:
                    dias_hasta = 7  # próxima semana si es el mismo día
                fecha_base = (ahora + timedelta(days=dias_hasta)).date()
                break

    # Detectar hora (ej: "a las 10", "a las 3 y media", "10am", "15:30")
    patron_hora = r"a\s+las\s+(\d{1,2})(?::(\d{2}))?\s*(?:(am|pm|de\s+la\s+ma[nñ]ana|de\s+la\s+tarde|de\s+la\s+noche))?"
    m = re.search(patron_hora, texto_norm)
    if m:
        hora = int(m.group(1))
        minutos = int(m.group(2)) if m.group(2) else 0
        modificador = m.group(3) or ""
        if ("pm" in modificador or "tarde" in modificador or "noche" in modificador) and hora < 12:
            hora += 12
        elif "am" in modificador and hora == 12:
            hora = 0
        hora_base = f"{hora:02d}:{minutos:02d}:00"

    if hora_base:
        return f"{fecha_base}T{hora_base}"
    elif fecha_base != ahora.date():
        return f"{fecha_base}T09:00:00"  # hora por defecto si solo se menciona el día

    return None


def _extraer_metodo_pago(texto: str) -> Optional[str]:
    """Extrae método de pago mencionado en el comando de voz."""
    texto_norm = texto.lower()
    if any(kw in texto_norm for kw in ["efectivo", "en cash", "en efectivo", "pago en efectivo"]):
        return "Efectivo"
    if any(kw in texto_norm for kw in ["tarjeta", "con tarjeta", "débito", "crédito", "debito", "credito"]):
        return "Tarjeta"
    return None


def _extraer_destinos_multiples(texto: str) -> list[str]:
    """Extrae lista de destinos para viajes con múltiples paradas."""
    texto_norm = texto.lower()
    destinos = []

    # Patrón: "primero a X, luego a Y, después a Z"
    patron = r"(?:primero\s+a|luego\s+a|despu[eé]s\s+a|tambi[eé]n\s+a|y\s+a|pasar\s+por)\s+([a-záéíóúüñ\s]+?)(?=\s*(?:,|\by\b|\bluego\b|\bdespu[eé]s\b|\btambi[eé]n\b|$))"
    matches = re.findall(patron, texto_norm)
    if matches:
        destinos = [m.strip().title() for m in matches if len(m.strip()) > 2]

    # Fallback: separar por "y" o ","
    if not destinos:
        partes = re.split(r"\s+y\s+|\s*,\s*", texto_norm)
        for p in partes:
            m = re.search(r"(?:al?|a)\s+([a-záéíóúüñ\s]{3,30})", p)
            if m:
                destinos.append(m.group(1).strip().title())

    return destinos


def _extraer_parada(texto: str) -> Optional[str]:
    """Extrae la parada a agregar en viajes múltiples."""
    patrones = [
        r"(?:parada\s+en|parar\s+en|pasando\s+por|también\s+ir\s+a|también\s+a|también\s+a)\s+([a-záéíóúüñ\s]+?)(?:\s*(?:,|$))",
        r"(?:agregar|añadir|agrega|añade)\s+(?:(?:una\s+)?parada\s+(?:en|a)?\s+)?([a-záéíóúüñ\s]{3,40})(?:\s*(?:,|$))",
    ]
    texto_norm = texto.lower()
    for patron in patrones:
        m = re.search(patron, texto_norm)
        if m:
            return m.group(1).strip().title()
    return None


def _extraer_nombre_acompanante(texto: str) -> Optional[str]:
    """Extrae el nombre del acompañante."""
    patrones = [
        r"(?:se\s+llama|llamado|llamada|nombre\s+es|nombre)\s+([A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+(?:\s+[A-ZÁÉÍÓÚÜÑ][a-záéíóúüñ]+)*)",
        r"(?:se\s+llama|llamado|llamada|nombre\s+es|nombre)\s+([a-záéíóúüñ]+(?:\s+[a-záéíóúüñ]+)*)",
    ]
    for patron in patrones:
        m = re.search(patron, texto, re.IGNORECASE)
        if m:
            return m.group(1).strip().title()
    return None


def _extraer_parentesco(texto: str) -> Optional[str]:
    """Extrae el parentesco del acompañante."""
    texto_norm = texto.lower()
    for parentesco in _PARENTESCOS:
        if re.search(rf"\b{parentesco}\b", texto_norm):
            return parentesco
    return None


# ──────────────────────────────────────────────
# Respuestas de voz en español
# ──────────────────────────────────────────────

def _generar_respuesta_voz(intencion: str, entidades: dict) -> str:
    """Genera una respuesta de texto natural para leer en voz alta."""
    if intencion == "solicitar_viaje":
        destino = entidades.get("destino")
        hora = entidades.get("fecha_hora_inicio")
        if destino and hora:
            return f"Entendido, preparando tu viaje a {destino}."
        elif destino:
            return f"Entendido, preparando tu viaje a {destino}. ¿A qué hora lo necesitas?"
        return "Entendido, voy a abrir el formulario para solicitar tu viaje."

    if intencion == "solicitar_viaje_multiple":
        destinos = entidades.get("destinos", [])
        if destinos:
            return f"Perfecto, viaje con {len(destinos)} paradas: {', '.join(destinos)}."
        return "Entendido, preparando tu viaje con múltiples paradas."

    if intencion == "cancelar_viaje":
        return "Entendido, voy a cancelar tu viaje."

    if intencion == "ver_viaje_actual":
        return "Aquí está el estado de tu viaje actual."

    if intencion == "ver_historial":
        return "Aquí está tu historial de viajes."

    if intencion == "crear_acompanante":
        nombre = entidades.get("nombre_completo")
        if nombre:
            return f"Registrando a {nombre} como acompañante."
        return "Voy a abrir el formulario para agregar un acompañante."

    if intencion == "ver_acompanantes":
        return "Aquí están tus acompañantes registrados."

    if intencion == "ver_pagos":
        return "Aquí están tus métodos de pago."

    if intencion == "ver_home":
        return "Regresando al inicio."

    if intencion == "ver_perfil":
        return "Aquí está tu perfil."

    if intencion == "confirmar":
        return "Entendido, confirmando."

    if intencion == "cancelar_accion":
        return "Cancelado."

    if intencion == "ir_atras":
        return "Regresando a la pantalla anterior."

    if intencion == "filtrar_completados":
        return "Mostrando solo viajes completados."

    if intencion == "filtrar_cancelados":
        return "Mostrando solo viajes cancelados."

    if intencion == "filtrar_todos":
        return "Mostrando todos los viajes."

    if intencion == "establecer_origen":
        origen = entidades.get("punto_inicio")
        if origen:
            return f"Origen establecido: {origen}."
        return "¿Desde dónde sales?"

    if intencion == "establecer_hora":
        hora = entidades.get("hora")
        minutos = entidades.get("minutos", "00")
        if hora:
            return f"Hora establecida: {hora}:{minutos}."
        return "¿A qué hora necesitas el viaje?"

    if intencion == "establecer_destino":
        destino = entidades.get("destino")
        if destino:
            return f"Destino establecido: {destino}."
        return "¿A dónde quieres ir?"

    if intencion == "agregar_parada":
        parada = entidades.get("parada")
        if parada:
            return f"Parada agregada: {parada}."
        return "¿En qué lugar quieres hacer una parada?"

    if intencion == "quitar_parada":
        return "Última parada eliminada."

    if intencion == "enviar_reporte":
        return "Enviando tu reporte."

    return "Lo siento, no entendí bien. ¿Puedes repetirlo?"


# ──────────────────────────────────────────────
# Mapeo intención → pantalla Flutter
# ──────────────────────────────────────────────

_PANTALLAS = {
    "solicitar_viaje": "crear_viaje",
    "solicitar_viaje_multiple": "crear_viaje_multiple",
    "cancelar_viaje": "cancelar_viaje",
    "ver_viaje_actual": "viaje_actual",
    "ver_historial": "historial",
    "crear_acompanante": "crear_acompanante",
    "ver_acompanantes": "mis_acompanantes",
    "ver_pagos": "metodos_pago",
    "ver_home": "home",
    "ver_perfil": "perfil",
    "confirmar": "confirmar",
    "cancelar_accion": "cancelar_accion",
    "ir_atras": "ir_atras",
    "filtrar_completados": "filtrar_completados",
    "filtrar_cancelados": "filtrar_cancelados",
    "filtrar_todos": "filtrar_todos",
    "establecer_origen": "establecer_origen",
    "establecer_hora": "establecer_hora",
    "establecer_destino": "establecer_destino",
    "agregar_parada": "agregar_parada",
    "quitar_parada": "quitar_parada",
    "enviar_reporte": "enviar_reporte",
}


# ──────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────

def interpretar_comando(texto: str) -> dict:
    """
    Interpreta un texto en español y devuelve intención + entidades + acción.

    Args:
        texto: Texto transcrito del comando de voz del pasajero.

    Returns:
        Diccionario con:
          - transcripcion: texto original
          - intencion: la acción que quiere realizar
          - confianza: nivel de certeza (0.0 - 1.0)
          - entidades: datos extraídos del texto
          - accion: pantalla y datos para que Flutter navegue
          - respuesta_voz: texto para leer en voz alta
    """
    intencion, confianza = detectar_intencion(texto)

    entidades: dict = {}

    if intencion == "solicitar_viaje":
        destino = _extraer_destino(texto)
        origen = _extraer_origen(texto)
        fecha_hora = _extraer_fecha_hora(texto)
        metodo_pago = _extraer_metodo_pago(texto)
        if destino:
            entidades["destino"] = destino
        if origen:
            entidades["punto_inicio"] = origen
        if fecha_hora:
            entidades["fecha_hora_inicio"] = fecha_hora
        if metodo_pago:
            entidades["metodo_pago"] = metodo_pago

    elif intencion == "solicitar_viaje_multiple":
        destinos = _extraer_destinos_multiples(texto)
        origen = _extraer_origen(texto)
        fecha_hora = _extraer_fecha_hora(texto)
        metodo_pago = _extraer_metodo_pago(texto)
        entidades["destinos"] = destinos
        entidades["check_destinos"] = True
        if origen:
            entidades["punto_inicio"] = origen
        if fecha_hora:
            entidades["fecha_hora_inicio"] = fecha_hora
        if metodo_pago:
            entidades["metodo_pago"] = metodo_pago

    elif intencion == "crear_acompanante":
        nombre = _extraer_nombre_acompanante(texto)
        parentesco = _extraer_parentesco(texto)
        if nombre:
            entidades["nombre_completo"] = nombre
        if parentesco:
            entidades["parentesco"] = parentesco

    elif intencion == "establecer_destino":
        destino = _extraer_destino(texto)
        if destino:
            entidades["destino"] = destino

    elif intencion == "establecer_origen":
        origen = _extraer_origen(texto)
        if origen:
            entidades["punto_inicio"] = origen

    elif intencion == "establecer_hora":
        hora_info = _extraer_hora_sola(texto)
        if hora_info:
            entidades["hora"] = hora_info["hora"]
            entidades["minutos"] = hora_info["minutos"]

    elif intencion == "agregar_parada":
        parada = _extraer_parada(texto)
        if parada:
            entidades["parada"] = parada

    pantalla = _PANTALLAS.get(intencion)
    respuesta_voz = _generar_respuesta_voz(intencion, entidades)

    return {
        "transcripcion": texto,
        "intencion": intencion,
        "confianza": confianza,
        "entidades": entidades,
        "accion": {
            "pantalla": pantalla,
            "datos_prellenados": entidades,
        },
        "respuesta_voz": respuesta_voz,
    }
