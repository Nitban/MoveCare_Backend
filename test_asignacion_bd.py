"""
Prueba de asignación de conductores con la BD real (Supabase).
Ejecutar desde: C:\\Users\\alelo\\ai-movecare\\backend
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

# Importar todos los modelos para que SQLAlchemy resuelva relaciones
from app.models.usuario_model import Usuario
from app.models.conductor_model import Conductor
from app.models.pasajero_model import Pasajero
from app.models.vehiculo_model import Vehiculos
from app.models.viaje_model import Viaje
from app.models.ubicacion_model import UbicacionConductor
from app.models.pagos_model import CuentaBancaria, MetodoPago
from app.models.acompanante_model import Acompanante

from app.core.database import SessionLocal
from app.ai.asignacion.asignacion_service import (
    _conductores_disponibles,
    asignar_conductores,
)

db = SessionLocal()

try:
    # ── 1. Ver conductores disponibles ──────────────
    print("\n" + "="*55)
    print("  CONDUCTORES DISPONIBLES")
    print("="*55)
    conductores = _conductores_disponibles(db)
    if not conductores:
        print("  No hay conductores disponibles.")
    for c in conductores:
        lat = f"{c['lat']:.4f}" if c['lat'] else "sin GPS"
        lon = f"{c['lon']:.4f}" if c['lon'] else "sin GPS"
        print(f"\n  {c['nombre']}")
        print(f"    Accesorios : {c['accesorios'] or 'ninguno'}")
        print(f"    Capacidad  : {c['capacidad']} pasajeros")
        print(f"    Rating     : {c['rating_avg'] or 'nuevo'}")
        print(f"    Ubicación  : {lat}, {lon}")

    # ── 2. Ver viajes pendientes ─────────────────────
    print("\n" + "="*55)
    print("  VIAJES PENDIENTES SIN CONDUCTOR")
    print("="*55)
    viajes = db.query(Viaje).filter(
        Viaje.estado == "Pendiente",
        Viaje.id_conductor == None
    ).all()
    if not viajes:
        print("  No hay viajes pendientes.")
    for v in viajes:
        print(f"\n  Viaje: {v.id_viaje}")
        print(f"    Origen  : {v.punto_inicio}")
        print(f"    Destino : {v.destino}")
        print(f"    Fecha   : {v.fecha_hora_inicio}")
        print(f"    Especif.: {v.especificaciones or 'ninguna'}")

    # ── 3. Ejecutar asignación ───────────────────────
    print("\n" + "="*55)
    print("  EJECUTANDO ALGORITMO DE ASIGNACIÓN...")
    print("="*55)
    resultado = asignar_conductores(db)

    print(f"\n  Viajes asignados: {resultado['asignados']}")

    if resultado.get("mensaje"):
        print(f"  Mensaje: {resultado['mensaje']}")

    for asig in resultado["detalle"]:
        print(f"\n  Viaje  : {asig['id_viaje']}")
        print(f"  Conductor asignado : {asig['nombre_conductor']}")
        print(f"  Compatibilidad     : {asig['puntaje_compatibilidad']*100:.1f}%")

    # ── 4. Verificar en BD ───────────────────────────
    print("\n" + "="*55)
    print("  ESTADO FINAL EN BD")
    print("="*55)
    viajes_post = db.query(Viaje).filter(
        Viaje.id_viaje.in_([v.id_viaje for v in viajes])
    ).all()
    for v in viajes_post:
        cond_nombre = "sin asignar"
        if v.conductor and v.conductor.usuario:
            cond_nombre = v.conductor.usuario.nombre_completo
        print(f"\n  Viaje {str(v.id_viaje)[:8]}...")
        print(f"    Estado    : {v.estado}")
        print(f"    Conductor : {cond_nombre}")

finally:
    db.close()
