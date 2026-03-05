"""
Módulo de puntuación para asignación de conductores.

Calcula el costo de asignar un conductor a un viaje considerando:
  - Compatibilidad de accesibilidad (discapacidad del pasajero vs accesorios del vehículo)
  - Distancia entre conductor y punto de inicio del viaje
  - Calificación promedio del conductor
  - Capacidad del vehículo para acompañantes
"""

import math
from typing import Optional


# Palabras clave de accesorios que cubren cada tipo de discapacidad
ACCESIBILIDAD_MAP: dict[str, list[str]] = {
    "motriz":       ["rampa", "silla de ruedas", "wheelchair", "anclaje", "elevador"],
    "visual":       ["audio", "braille", "narrador", "sonido"],
    "auditiva":     ["pantalla", "visual", "vibración", "led"],
    "adulto_mayor": [],   # cualquier vehículo es aceptable
    "obesidad":     ["amplio", "reforzado", "bariátrico"],
}


def puntaje_accesibilidad(discapacidad: Optional[str], accesorios: Optional[str]) -> float:
    """
    Retorna un valor entre 0.0 y 1.0.
    1.0 → vehículo completamente compatible
    0.5 → compatibilidad parcial
    0.0 → incompatible (penalización máxima)
    """
    if not discapacidad:
        return 1.0

    clave = discapacidad.strip().lower()
    keywords = ACCESIBILIDAD_MAP.get(clave, [])

    if not keywords:
        return 1.0

    texto_accesorios = (accesorios or "").lower()

    # Basta con que el vehículo tenga AL MENOS UNO de los accesorios requeridos
    if any(kw in texto_accesorios for kw in keywords):
        return 1.0
    return 0.0


def puntaje_rating(rating_promedio: Optional[float]) -> float:
    """Normaliza calificación 0–5 a 0–1. Conductores nuevos reciben 0.7."""
    if rating_promedio is None:
        return 0.7
    return max(0.0, min(rating_promedio / 5.0, 1.0))


def distancia_haversine(lat1: Optional[float], lon1: Optional[float],
                        lat2: Optional[float], lon2: Optional[float]) -> float:
    """
    Distancia en km entre dos coordenadas usando la fórmula de Haversine.
    Retorna 999.0 si faltan coordenadas.
    """
    if None in (lat1, lon1, lat2, lon2):
        return 999.0

    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def puntaje_distancia(distancia_km: float, radio_max_km: float = 20.0) -> float:
    """Mayor proximidad = mayor puntaje. Fuera del radio máximo → 0."""
    if distancia_km >= radio_max_km:
        return 0.0
    return 1.0 - (distancia_km / radio_max_km)


def puntaje_capacidad(capacidad: Optional[int], con_acompanante: bool) -> float:
    """Penaliza si el viaje requiere acompañante y el vehículo tiene poca capacidad."""
    if not con_acompanante:
        return 1.0
    if capacidad and capacidad >= 2:
        return 1.0
    return 0.4


def calcular_costo(
    discapacidad: Optional[str],
    accesorios: Optional[str],
    rating_promedio: Optional[float],
    lat_conductor: Optional[float],
    lon_conductor: Optional[float],
    lat_viaje: Optional[float],
    lon_viaje: Optional[float],
    capacidad: Optional[int],
    con_acompanante: bool,
) -> float:
    """
    Retorna el COSTO de asignación (0 = mejor, 1 = peor).
    El algoritmo húngaro minimiza la suma de costos de la matriz.

    Pesos:
      Accesibilidad : 40%
      Distancia     : 35%
      Rating        : 15%
      Capacidad     :10%
    """
    distancia_km = distancia_haversine(lat_conductor, lon_conductor, lat_viaje, lon_viaje)

    score = (
        0.40 * puntaje_accesibilidad(discapacidad, accesorios)
        + 0.35 * puntaje_distancia(distancia_km)
        + 0.15 * puntaje_rating(rating_promedio)
        + 0.10 * puntaje_capacidad(capacidad, con_acompanante)
    )

    return round(1.0 - score, 4)  # Invertir: mayor score → menor costo
