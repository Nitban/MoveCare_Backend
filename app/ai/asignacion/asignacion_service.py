"""
Servicio de asignación inteligente de conductores.

Flujo:
  1. Obtener viajes en estado "Pendiente" sin conductor asignado
  2. Obtener conductores disponibles (activos, sin viaje activo)
  3. Construir matriz de costos [viajes × conductores]
  4. Resolver asignación óptima con el algoritmo húngaro (scipy)
  5. Actualizar los viajes asignados en BD
"""

from __future__ import annotations

from typing import Optional
from uuid import UUID

import numpy as np
from scipy.optimize import linear_sum_assignment
from sqlalchemy import and_
from sqlalchemy.orm import Session

from app.ai.asignacion.scoring import calcular_costo
from app.models.conductor_model import Conductor
from app.models.pasajero_model import Pasajero
from app.models.ubicacion_model import UbicacionConductor
from app.models.usuario_model import Usuario
from app.models.vehiculo_model import Vehiculos
from app.models.viaje_model import Viaje


# ──────────────────────────────────────────────
# Helpers internos
# ──────────────────────────────────────────────

def _conductores_disponibles(db: Session) -> list[dict]:
    """
    Devuelve conductores activos que no tienen un viaje En_curso o Agendado.
    Incluye datos de vehículo y última ubicación conocida.
    """
    ocupados = (
        db.query(Viaje.id_conductor)
        .filter(
            Viaje.estado.in_(["En_curso", "Agendado"]),
            Viaje.id_conductor.isnot(None),
        )
        .scalar_subquery()
    )

    filas = (
        db.query(Conductor, Usuario, Vehiculos, UbicacionConductor)
        .join(Usuario, Conductor.id_usuario == Usuario.id_usuario)
        .outerjoin(
            Vehiculos,
            and_(
                Vehiculos.id_conductor == Conductor.id_conductor,
                Vehiculos.activo == True,
            ),
        )
        .outerjoin(
            UbicacionConductor,
            UbicacionConductor.id_conductor == Conductor.id_conductor,
        )
        .filter(
            Usuario.activo == True,
            ~Conductor.id_conductor.in_(ocupados),
        )
        .all()
    )

    conductores = []
    visto = set()
    for c, u, v, ub in filas:
        # outerjoin puede producir duplicados si hay varios vehículos; tomamos el primero
        if c.id_conductor in visto:
            continue
        visto.add(c.id_conductor)

        rating = (
            db.query(
                db.query(Viaje.cal_conductor)
                .filter(
                    Viaje.id_conductor == c.id_conductor,
                    Viaje.cal_conductor.isnot(None),
                )
                .subquery()
            ).count()
        )
        # Calcular promedio de calificación
        from sqlalchemy import func as sa_func
        rating_avg = db.query(sa_func.avg(Viaje.cal_conductor)).filter(
            Viaje.id_conductor == c.id_conductor,
            Viaje.cal_conductor.isnot(None),
        ).scalar()

        conductores.append(
            {
                "id_conductor": c.id_conductor,
                "nombre": u.nombre_completo,
                "accesorios": v.accesorios if v else None,
                "capacidad": v.capacidad if v else None,
                "rating_avg": float(rating_avg) if rating_avg else None,
                "lat": ub.latitud if ub else None,
                "lon": ub.longitud if ub else None,
            }
        )

    return conductores


def _coordenadas_viaje(viaje: Viaje) -> tuple[Optional[float], Optional[float]]:
    """
    Extrae lat/lon del punto de inicio del viaje.
    Busca en el campo `ruta` (JSONB) primero, luego en `destinos`.
    """
    if viaje.ruta and isinstance(viaje.ruta, dict):
        inicio = viaje.ruta.get("inicio", {})
        lat = inicio.get("lat") or inicio.get("latitud")
        lon = inicio.get("lon") or inicio.get("longitud")
        if lat and lon:
            return float(lat), float(lon)

    # Si el viaje tiene destinos JSONB, el primero suele ser el punto de inicio
    if viaje.destinos and isinstance(viaje.destinos, list) and viaje.destinos:
        primero = viaje.destinos[0]
        if isinstance(primero, dict):
            lat = primero.get("lat") or primero.get("latitud")
            lon = primero.get("lon") or primero.get("longitud")
            if lat and lon:
                return float(lat), float(lon)

    return None, None


# ──────────────────────────────────────────────
# API pública
# ──────────────────────────────────────────────

def asignar_conductores(
    db: Session,
    ids_viaje: Optional[list[str]] = None,
) -> dict:
    """
    Asigna conductores a viajes Pendiente usando el algoritmo húngaro.

    Args:
        db: Sesión de base de datos.
        ids_viaje: Lista de UUIDs específicos a procesar.
                   Si es None, procesa todos los viajes Pendiente sin conductor.

    Returns:
        Diccionario con cantidad asignada y detalle de cada asignación.
    """
    # 1. Viajes pendientes
    query = db.query(Viaje).filter(
        Viaje.estado == "Pendiente",
        Viaje.id_conductor.is_(None),
    )
    if ids_viaje:
        query = query.filter(Viaje.id_viaje.in_(ids_viaje))
    viajes = query.all()

    if not viajes:
        return {"asignados": 0, "detalle": [], "mensaje": "No hay viajes pendientes"}

    # 2. Conductores disponibles
    conductores = _conductores_disponibles(db)
    if not conductores:
        return {"asignados": 0, "detalle": [], "mensaje": "No hay conductores disponibles"}

    # 3. Info de pasajeros para cada viaje
    trips_info = []
    for v in viajes:
        pasajero = db.query(Pasajero).filter(Pasajero.id_pasajero == v.id_pasajero).first()
        usuario = (
            db.query(Usuario).filter(Usuario.id_usuario == pasajero.id_usuario).first()
            if pasajero
            else None
        )
        lat, lon = _coordenadas_viaje(v)
        trips_info.append(
            {
                "viaje": v,
                "discapacidad": usuario.discapacidad if usuario else None,
                "lat": lat,
                "lon": lon,
            }
        )

    # 4. Matriz de costos [n_viajes × n_conductores]
    n_v = len(trips_info)
    n_c = len(conductores)
    cost_matrix = np.zeros((n_v, n_c))

    for i, ti in enumerate(trips_info):
        for j, c in enumerate(conductores):
            cost_matrix[i, j] = calcular_costo(
                discapacidad=ti["discapacidad"],
                accesorios=c["accesorios"],
                rating_promedio=c["rating_avg"],
                lat_conductor=c["lat"],
                lon_conductor=c["lon"],
                lat_viaje=ti["lat"],
                lon_viaje=ti["lon"],
                capacidad=c["capacidad"],
                con_acompanante=bool(ti["viaje"].check_acompanante),
            )

    # 5. Algoritmo húngaro
    filas, cols = linear_sum_assignment(cost_matrix)

    # 6. Aplicar asignaciones válidas (costo < 0.95 evita pares incompatibles)
    UMBRAL_COSTO = 0.95
    asignaciones = []

    for fila, col in zip(filas, cols):
        costo = cost_matrix[fila, col]
        if costo >= UMBRAL_COSTO:
            continue

        viaje = trips_info[fila]["viaje"]
        conductor = conductores[col]

        viaje.id_conductor = conductor["id_conductor"]
        viaje.estado = "Agendado"
        db.add(viaje)

        asignaciones.append(
            {
                "id_viaje": str(viaje.id_viaje),
                "id_conductor": str(conductor["id_conductor"]),
                "nombre_conductor": conductor["nombre"],
                "puntaje_compatibilidad": round(1.0 - costo, 3),
            }
        )

    db.commit()

    return {
        "asignados": len(asignaciones),
        "detalle": asignaciones,
    }


def actualizar_ubicacion(
    db: Session,
    id_conductor: UUID,
    latitud: float,
    longitud: float,
) -> UbicacionConductor:
    """
    Crea o actualiza la ubicación en tiempo real de un conductor.
    Usa upsert lógico: si ya existe el registro lo actualiza, si no lo crea.
    """
    ubicacion = (
        db.query(UbicacionConductor)
        .filter(UbicacionConductor.id_conductor == id_conductor)
        .first()
    )

    if ubicacion:
        ubicacion.latitud = latitud
        ubicacion.longitud = longitud
    else:
        ubicacion = UbicacionConductor(
            id_conductor=id_conductor,
            latitud=latitud,
            longitud=longitud,
        )
        db.add(ubicacion)

    db.commit()
    db.refresh(ubicacion)
    return ubicacion
