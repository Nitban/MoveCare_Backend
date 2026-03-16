"""
Router de Inteligencia Artificial
Endpoints:
  POST /ia/conductores/ubicacion        → Conductor actualiza su posición GPS
  GET  /ia/conductores/disponibles      → Admin: lista conductores sin viaje activo
  POST /ia/viajes/asignar               → Admin: asigna conductores a TODOS los viajes pendientes
  POST /ia/viajes/{id_viaje}/asignar    → Admin: asigna conductor a un viaje específico
  GET  /ia/demo                         → Demo pública del algoritmo de asignación
  POST /ia/rutas/calcular               → Calcula ruta óptima entre dos puntos (OSMnx)
  POST /ia/rutas/optimizar              → Ordena múltiples paradas de forma óptima
  GET  /ia/rutas/viaje/{id_viaje}       → Calcula ruta para un viaje existente en BD
"""

from uuid import UUID

import numpy as np
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from scipy.optimize import linear_sum_assignment
from sqlalchemy.orm import Session

from app.ai.rutas.rutas_service import (
    calcular_ruta,
    calcular_ruta_viaje,
    optimizar_paradas,
)
from app.ai.asignacion.asignacion_service import (
    _conductores_disponibles,
    _coordenadas_viaje,
    actualizar_ubicacion,
    asignar_conductores,
)
from app.ai.asignacion.scoring import (
    calcular_costo,
    distancia_haversine,
    puntaje_accesibilidad,
    puntaje_capacidad,
    puntaje_distancia,
    puntaje_rating,
)
from app.core.database import get_db
from app.dependencies.auth_dependencies import require_admin, require_conductor
from app.models.conductor_model import Conductor
from app.models.pasajero_model import Pasajero
from app.models.usuario_model import Usuario
from app.models.viaje_model import Viaje

router = APIRouter(prefix="/ia", tags=["Inteligencia Artificial"])


# ──────────────────────────────────────────────
# Schemas
# ──────────────────────────────────────────────

class UbicacionPayload(BaseModel):
    latitud: float = Field(..., ge=-90, le=90, description="Latitud WGS-84")
    longitud: float = Field(..., ge=-180, le=180, description="Longitud WGS-84")


class AsignarViajesPayload(BaseModel):
    ids_viaje: list[str] | None = Field(
        default=None,
        description="UUIDs de viajes a procesar. Omitir para procesar todos los pendientes.",
    )


class RutaSimplePayload(BaseModel):
    origen: str = Field(..., description="Dirección o lugar de origen", example="Guadalajara Centro")
    destino: str = Field(..., description="Dirección o lugar de destino", example="Zapopan Centro")


class RutaMultiplePayload(BaseModel):
    origen: str = Field(..., description="Punto de partida", example="Guadalajara Centro")
    paradas: list[str] = Field(
        ...,
        min_length=2,
        max_length=5,
        description="Lista de paradas a visitar (2–5 destinos)",
        example=["Tlaquepaque", "Tonalá", "Tlajomulco"],
    )


# ──────────────────────────────────────────────
# Endpoints
# ──────────────────────────────────────────────

@router.post("/conductores/ubicacion", summary="Actualizar ubicación del conductor")
def actualizar_ubicacion_conductor(
    payload: UbicacionPayload,
    db: Session = Depends(get_db),
    user=Depends(require_conductor),
):
    """
    El conductor envía sus coordenadas GPS actuales.
    Se usa para calcular la distancia en la asignación de viajes.
    Debe llamarse cada vez que la app del conductor actualice la posición.
    """
    conductor = (
        db.query(Conductor)
        .filter(Conductor.id_usuario == user["id_usuario"])
        .first()
    )
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")

    actualizar_ubicacion(
        db=db,
        id_conductor=conductor.id_conductor,
        latitud=payload.latitud,
        longitud=payload.longitud,
    )

    return {"ok": True, "mensaje": "Ubicación actualizada"}


@router.get("/conductores/disponibles", summary="Listar conductores disponibles")
def listar_conductores_disponibles(
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Devuelve todos los conductores activos que no tienen un viaje en curso o agendado.
    Incluye su última ubicación conocida y rating promedio.
    """
    conductores = _conductores_disponibles(db)
    return {"total": len(conductores), "conductores": conductores}


@router.post("/viajes/asignar", summary="Asignar conductores a viajes pendientes")
def asignar_viajes(
    payload: AsignarViajesPayload = AsignarViajesPayload(),
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Ejecuta el algoritmo húngaro para asignar el conductor óptimo
    a cada viaje en estado Pendiente.

    - Si se proporcionan ids_viaje, solo procesa esos viajes.
    - Si se omite, procesa todos los viajes Pendiente sin conductor.

    El conductor asignado se selecciona según:
      1. Compatibilidad de accesibilidad (40%)
      2. Proximidad al punto de inicio (35%)
      3. Calificación promedio (15%)
      4. Capacidad para acompañantes (10%)
    """
    try:
        resultado = asignar_conductores(db=db, ids_viaje=payload.ids_viaje)
        return {"ok": True, **resultado}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en asignación: {str(e)}")


@router.get("/demo", summary="🎓 Demo pública del algoritmo de asignación (sin autenticación)")
def demo_asignacion(db: Session = Depends(get_db)):
    """
    **Demostración pública** del Algoritmo Húngaro de Asignación Inteligente.

    No requiere autenticación. Muestra en detalle cómo el sistema evalúa
    cada combinación conductor–viaje y selecciona la asignación globalmente óptima.

    Criterios de puntuación:
    - **Accesibilidad** (40%): accesorios del vehículo vs necesidades del pasajero
    - **Proximidad** (35%): distancia Haversine conductor → punto de inicio
    - **Calificación** (15%): rating promedio del conductor
    - **Capacidad** (10%): capacidad para acompañantes si aplica

    > Ejecuta `seed_prueba.py` para cargar datos de prueba antes de usar este endpoint.
    """
    # 1. Obtener viajes pendientes
    viajes = db.query(Viaje).filter(
        Viaje.estado == "Pendiente",
        Viaje.id_conductor.is_(None),
    ).all()

    if not viajes:
        return {
            "estado": "sin_datos",
            "mensaje": "No hay viajes pendientes. Ejecuta: python seed_prueba.py",
        }

    # 2. Obtener conductores disponibles
    conductores = _conductores_disponibles(db)
    if not conductores:
        return {
            "estado": "sin_datos",
            "mensaje": "No hay conductores disponibles.",
        }

    # 3. Construir info de pasajeros
    trips_info = []
    for v in viajes:
        pasajero = db.query(Pasajero).filter(Pasajero.id_pasajero == v.id_pasajero).first()
        usuario = (
            db.query(Usuario).filter(Usuario.id_usuario == pasajero.id_usuario).first()
            if pasajero else None
        )
        lat, lon = _coordenadas_viaje(v)
        trips_info.append({
            "viaje": v,
            "pasajero_nombre": usuario.nombre_completo if usuario else "Desconocido",
            "discapacidad": usuario.discapacidad if usuario else None,
            "lat": lat,
            "lon": lon,
        })

    # 4. Construir matriz de costos + desglose detallado
    n_v, n_c = len(trips_info), len(conductores)
    cost_matrix = np.zeros((n_v, n_c))
    evaluacion = []

    for i, ti in enumerate(trips_info):
        candidatos = []
        for j, c in enumerate(conductores):
            dist_km = distancia_haversine(c["lat"], c["lon"], ti["lat"], ti["lon"])
            s_acc   = puntaje_accesibilidad(ti["discapacidad"], c["accesorios"])
            s_dist  = puntaje_distancia(dist_km)
            s_rat   = puntaje_rating(c["rating_avg"])
            s_cap   = puntaje_capacidad(c["capacidad"], bool(ti["viaje"].check_acompanante))
            compat  = round((0.40*s_acc + 0.35*s_dist + 0.15*s_rat + 0.10*s_cap) * 100, 1)
            costo   = round(1.0 - compat/100, 4)
            cost_matrix[i, j] = costo

            candidatos.append({
                "conductor": c["nombre"],
                "vehiculo_accesorios": c["accesorios"] or "Sin accesorios registrados",
                "scores": {
                    "accesibilidad": f"{round(s_acc*100)}%",
                    "distancia_km": round(dist_km, 2) if dist_km < 900 else "GPS no disponible",
                    "distancia": f"{round(s_dist*100)}%",
                    "calificacion": f"{round(s_rat*100)}%",
                    "capacidad": f"{round(s_cap*100)}%",
                },
                "compatibilidad_total": f"{compat}%",
            })

        # Ordenar candidatos de mayor a menor compatibilidad para la vista
        candidatos.sort(key=lambda x: x["compatibilidad_total"], reverse=True)

        evaluacion.append({
            "viaje_id": str(ti["viaje"].id_viaje),
            "pasajero": ti["pasajero_nombre"],
            "necesidad_especial": ti["discapacidad"] or "Ninguna",
            "candidatos_evaluados": candidatos,
        })

    # 5. Algoritmo húngaro (solo lectura, NO guarda en BD)
    filas, cols = linear_sum_assignment(cost_matrix)
    asignaciones_optimas = []
    for fila, col in zip(filas, cols):
        costo = cost_matrix[fila, col]
        if costo >= 0.95:
            continue
        ti = trips_info[fila]
        c  = conductores[col]
        asignaciones_optimas.append({
            "viaje": f"Pasajero: {ti['pasajero_nombre']} | Necesidad: {ti['discapacidad'] or 'Ninguna'}",
            "conductor_asignado": c["nombre"],
            "compatibilidad": f"{round((1-costo)*100, 1)}%",
            "vehiculo": c["accesorios"] or "Sin accesorios",
        })

    return {
        "titulo": "Algoritmo Húngaro — Asignación Inteligente de Conductores MoveCare",
        "resumen": {
            "viajes_pendientes": n_v,
            "conductores_disponibles": n_c,
            "asignaciones_realizadas": len(asignaciones_optimas),
        },
        "evaluacion_detallada": evaluacion,
        "asignacion_optima_final": asignaciones_optimas,
        "nota": (
            "El Algoritmo Húngaro garantiza la asignación GLOBALMENTE óptima: "
            "minimiza el costo total de la matriz, no solo cada par individualmente. "
            "Este endpoint es de solo lectura — para aplicar las asignaciones usar POST /ia/viajes/asignar."
        ),
    }


@router.post("/viajes/{id_viaje}/asignar", summary="Asignar conductor a un viaje específico")
def asignar_viaje_especifico(
    id_viaje: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Variante que asigna el conductor óptimo a un único viaje.
    Útil para reasignaciones o cuando se crea un viaje urgente.
    """
    try:
        resultado = asignar_conductores(db=db, ids_viaje=[id_viaje])
        if resultado["asignados"] == 0:
            raise HTTPException(
                status_code=422,
                detail=resultado.get("mensaje", "No se pudo asignar conductor"),
            )
        return {"ok": True, **resultado}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en asignación: {str(e)}")


# ──────────────────────────────────────────────
# Rutas (OpenStreetMap + NetworkX)
# ──────────────────────────────────────────────

@router.post("/rutas/calcular", summary="Calcular ruta óptima entre dos puntos")
def calcular_ruta_endpoint(payload: RutaSimplePayload):
    """
    Calcula la ruta más corta en la **red vial real de OpenStreetMap** entre
    origen y destino.

    - Geocodifica ambas direcciones con Nominatim (OSM, sin Google Maps)
    - Descarga el grafo vial del área usando OSMnx
    - Aplica el algoritmo de Dijkstra (NetworkX) para encontrar la ruta más corta
    - Devuelve waypoints, distancia en km y duración estimada en minutos

    > La primera llamada puede tardar unos segundos mientras se descarga el grafo.
    """
    try:
        resultado = calcular_ruta(payload.origen, payload.destino)
        return {"ok": True, **resultado}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular ruta: {str(e)}")


@router.post("/rutas/optimizar", summary="Optimizar orden de múltiples paradas")
def optimizar_ruta_endpoint(payload: RutaMultiplePayload):
    """
    Para viajes con **2 a 5 paradas**, calcula el orden de visita óptimo
    usando el algoritmo de **Vecino Más Cercano** (Nearest Neighbor Heuristic).

    - Geocodifica cada parada con Nominatim/OSM
    - Ordena las paradas minimizando la distancia total recorrida
    - Calcula la ruta real (red vial OSM) para cada segmento
    - Devuelve el orden sugerido, distancia total y desglose por tramo

    Ideal para `check_destinos = true` en el modelo de viaje.
    """
    try:
        resultado = optimizar_paradas(payload.origen, payload.paradas)
        return {"ok": True, **resultado}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al optimizar paradas: {str(e)}")


@router.get("/rutas/viaje/{id_viaje}", summary="Calcular ruta para un viaje existente")
def ruta_para_viaje(
    id_viaje: str,
    db: Session = Depends(get_db),
    _=Depends(require_admin),
):
    """
    Calcula la ruta óptima para un viaje ya registrado en la base de datos.

    - Si `check_destinos = false`: ruta simple `punto_inicio → destino`
    - Si `check_destinos = true`: optimiza el orden de todas las paradas en `destinos`

    Los resultados pueden guardarse de vuelta en el campo `ruta` (JSONB) del viaje.
    """
    viaje = db.query(Viaje).filter(Viaje.id_viaje == id_viaje).first()
    if not viaje:
        raise HTTPException(status_code=404, detail="Viaje no encontrado")

    try:
        resultado = calcular_ruta_viaje(viaje)
        return {"ok": True, "id_viaje": id_viaje, **resultado}
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al calcular ruta del viaje: {str(e)}")
