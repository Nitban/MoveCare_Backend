"""
Módulo de optimización de rutas usando OpenStreetMap (OSMnx + NetworkX).

Funciones principales:
  - geocodificar(lugar)                        → (lat, lon) vía Nominatim/OSM
  - calcular_ruta(origen, destino)             → ruta más corta en red vial real
  - optimizar_paradas(origen, paradas)         → orden óptimo para múltiples destinos
  - calcular_ruta_viaje(viaje, db)             → ruta para un viaje existente en BD
"""

from __future__ import annotations

import math
from typing import Optional

import networkx as nx
import osmnx as ox

# ──────────────────────────────────────────────
# Configuración OSMnx
# ──────────────────────────────────────────────

ox.settings.log_console = False
ox.settings.use_cache = True        # Cachea grafos descargados en disco
ox.settings.cache_folder = "./osmnx_cache"

# Velocidades promedio en km/h por tipo de vía (para tiempo estimado)
VELOCIDADES_VIA: dict[str, float] = {
    "motorway": 90,
    "trunk": 70,
    "primary": 50,
    "secondary": 40,
    "tertiary": 30,
    "residential": 25,
    "unclassified": 25,
    "service": 15,
}
VELOCIDAD_DEFAULT = 25.0  # km/h para calles sin clasificar


# ──────────────────────────────────────────────
# Geocodificación
# ──────────────────────────────────────────────

def geocodificar(lugar: str) -> tuple[float, float]:
    """
    Convierte una dirección de texto a coordenadas (lat, lon) usando Nominatim/OSM.
    Agrega contexto de Jalisco, México para mejorar precisión en la ZMG.

    Returns:
        (latitud, longitud)

    Raises:
        ValueError: si Nominatim no encuentra la dirección.
    """
    consultas = [
        f"{lugar}, Guadalajara, Jalisco, México",
        f"{lugar}, Jalisco, México",
        lugar,
    ]
    for consulta in consultas:
        try:
            resultado = ox.geocode(consulta)
            if resultado:
                return float(resultado[0]), float(resultado[1])
        except Exception:
            continue

    raise ValueError(
        f"No se pudo geocodificar la dirección: '{lugar}'. "
        "Verifica que sea una ubicación válida en la ZMG."
    )


# ──────────────────────────────────────────────
# Construcción del grafo vial
# ──────────────────────────────────────────────

def _grafo_entre_puntos(
    lat_o: float, lon_o: float,
    lat_d: float, lon_d: float,
    buffer_km: float = 1.5,
) -> nx.MultiDiGraph:
    """
    Descarga el grafo de calles de OSM en el área que cubre origen y destino.
    Usa un bounding box con margen para garantizar que exista ruta.
    """
    distancia_km = _haversine(lat_o, lon_o, lat_d, lon_d)
    radio_m = max(2000, int((distancia_km / 2 + buffer_km) * 1000))

    lat_centro = (lat_o + lat_d) / 2
    lon_centro = (lon_o + lon_d) / 2

    G = ox.graph_from_point(
        (lat_centro, lon_centro),
        dist=radio_m,
        network_type="drive",
        simplify=True,
    )
    return G


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distancia en km entre dos puntos usando la fórmula de Haversine."""
    R = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


# ──────────────────────────────────────────────
# Ruta más corta (un destino)
# ──────────────────────────────────────────────

def calcular_ruta(origen: str, destino: str) -> dict:
    """
    Calcula la ruta más corta en la red vial real de OpenStreetMap entre
    origen y destino (texto libre).

    Returns:
        {
            "origen": str,
            "destino": str,
            "distancia_km": float,
            "duracion_estimada_min": int,
            "waypoints": [{"lat": float, "lon": float}, ...],
            "total_nodos": int,
        }
    """
    lat_o, lon_o = geocodificar(origen)
    lat_d, lon_d = geocodificar(destino)

    G = _grafo_entre_puntos(lat_o, lon_o, lat_d, lon_d)

    nodo_o = ox.distance.nearest_nodes(G, lon_o, lat_o)
    nodo_d = ox.distance.nearest_nodes(G, lon_d, lat_d)

    try:
        ruta_nodos = nx.shortest_path(G, nodo_o, nodo_d, weight="length")
    except nx.NetworkXNoPath:
        raise ValueError(
            f"No se encontró ruta vial entre '{origen}' y '{destino}'. "
            "Las ubicaciones pueden estar en zonas sin conexión vial."
        )

    # Calcular distancia total en metros
    longitud_m = sum(
        G[ruta_nodos[i]][ruta_nodos[i + 1]][0].get("length", 0)
        for i in range(len(ruta_nodos) - 1)
    )

    # Estimar duración por tipo de vía
    duracion_seg = _estimar_duracion(G, ruta_nodos)

    # Extraer waypoints (coordenadas de cada nodo de la ruta)
    waypoints = [
        {"lat": round(G.nodes[n]["y"], 6), "lon": round(G.nodes[n]["x"], 6)}
        for n in ruta_nodos
    ]

    minutos = round(duracion_seg / 60)
    horas = minutos // 60
    mins_restantes = minutos % 60
    duracion_texto = (
        f"{horas} h {mins_restantes} min" if horas > 0 else f"{minutos} min"
    )

    return {
        "origen": origen,
        "destino": destino,
        "coordenadas_origen": {"lat": lat_o, "lon": lon_o},
        "coordenadas_destino": {"lat": lat_d, "lon": lon_d},
        "distancia_km": round(longitud_m / 1000, 2),
        "duracion_estimada_min": minutos,
        "duracion_estimada_texto": duracion_texto,
        "waypoints": waypoints,
        "total_nodos": len(ruta_nodos),
    }


def _estimar_duracion(G: nx.MultiDiGraph, ruta_nodos: list) -> float:
    """Estima duración en segundos según tipo de vía de cada segmento."""
    total_seg = 0.0
    for i in range(len(ruta_nodos) - 1):
        datos_arista = G[ruta_nodos[i]][ruta_nodos[i + 1]][0]
        longitud_m = datos_arista.get("length", 0)
        tipo_via = datos_arista.get("highway", "unclassified")
        if isinstance(tipo_via, list):
            tipo_via = tipo_via[0]
        velocidad = VELOCIDADES_VIA.get(tipo_via, VELOCIDAD_DEFAULT)
        total_seg += (longitud_m / 1000) / velocidad * 3600
    return total_seg


# ──────────────────────────────────────────────
# Optimización de múltiples paradas
# ──────────────────────────────────────────────

def optimizar_paradas(origen: str, paradas: list[str]) -> dict:
    """
    Calcula el orden óptimo de visita para múltiples paradas (2–5) usando
    el algoritmo de vecino más cercano (Nearest Neighbor Heuristic).

    Para el número de paradas típico en MoveCare (2–5), este algoritmo
    produce resultados muy cercanos al óptimo sin complejidad exponencial.

    Returns:
        {
            "orden_optimo": [str, ...],          # paradas en orden sugerido
            "distancia_total_km": float,
            "duracion_total_min": int,
            "segmentos": [
                {"de": str, "a": str, "distancia_km": float, "duracion_min": int}
            ]
        }
    """
    todos_los_puntos = [origen] + paradas
    coords = [geocodificar(p) for p in todos_los_puntos]

    # Nearest Neighbor partiendo desde el origen (índice 0)
    orden_indices = [0]
    no_visitados = list(range(1, len(todos_los_puntos)))

    while no_visitados:
        actual = orden_indices[-1]
        lat_a, lon_a = coords[actual]
        mas_cercano = min(
            no_visitados,
            key=lambda i: _haversine(lat_a, lon_a, coords[i][0], coords[i][1]),
        )
        orden_indices.append(mas_cercano)
        no_visitados.remove(mas_cercano)

    orden_nombres = [todos_los_puntos[i] for i in orden_indices]

    # Calcular ruta real segmento a segmento
    segmentos = []
    distancia_total = 0.0
    duracion_total = 0

    for i in range(len(orden_nombres) - 1):
        seg = calcular_ruta(orden_nombres[i], orden_nombres[i + 1])
        distancia_total += seg["distancia_km"]
        duracion_total += seg["duracion_estimada_min"]
        segmentos.append({
            "de": orden_nombres[i],
            "a": orden_nombres[i + 1],
            "distancia_km": seg["distancia_km"],
            "duracion_min": seg["duracion_estimada_min"],
            "waypoints": seg["waypoints"],
        })

    horas = duracion_total // 60
    mins_restantes = duracion_total % 60
    duracion_texto = (
        f"{horas} h {mins_restantes} min" if horas > 0 else f"{duracion_total} min"
    )

    return {
        "orden_optimo": orden_nombres,
        "distancia_total_km": round(distancia_total, 2),
        "duracion_total_min": duracion_total,
        "duracion_total_texto": duracion_texto,
        "segmentos": segmentos,
    }


# ──────────────────────────────────────────────
# Utilidad: ruta para un viaje existente en BD
# ──────────────────────────────────────────────

def calcular_ruta_viaje(viaje) -> dict:
    """
    Calcula y devuelve la ruta para un objeto Viaje de SQLAlchemy.
    Usa `punto_inicio` / `destino` para un viaje simple,
    o `destinos` JSONB para viajes con múltiples paradas.
    """
    if viaje.check_destinos and viaje.destinos:
        paradas = [d.get("direccion", "") for d in viaje.destinos if d.get("direccion")]
        if not paradas:
            raise ValueError("El viaje tiene check_destinos=True pero sin direcciones en 'destinos'.")
        return optimizar_paradas(viaje.punto_inicio, paradas)
    else:
        return calcular_ruta(viaje.punto_inicio, viaje.destino)
