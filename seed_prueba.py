"""
Script de datos de prueba para validar la IA de asignación de conductores.

Inserta en Supabase:
  - 1 usuario administrador
  - 1 usuario pasajero  (con discapacidad motriz)
  - 3 usuarios conductores (con distintos vehículos y accesorios)
  - 3 vehículos (uno con rampa, uno sin accesorios, uno nuevo)
  - 2 ubicaciones GPS de conductores (en Guadalajara)
  - 2 viajes en estado Pendiente

IMPORTANTE: Los usuarios NO se crean en Firebase, solo en la BD local.
Úsalos únicamente para probar la asignación de IA.

Para limpiar los datos insertados al terminar:
  python seed_prueba.py --limpiar

Ejecutar desde: C:\\Users\\alelo\\ai-movecare\\backend
"""

import sys
import os
import argparse
import uuid
from datetime import datetime

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from app.models.usuario_model import Usuario
from app.models.conductor_model import Conductor
from app.models.pasajero_model import Pasajero
from app.models.vehiculo_model import Vehiculos
from app.models.viaje_model import Viaje
from app.models.ubicacion_model import UbicacionConductor
from app.models.pagos_model import CuentaBancaria, MetodoPago  # necesario para resolver relaciones SQLAlchemy
from app.models.acompanante_model import Acompanante

# ─────────────────────────────────────────────────
# IDs fijos para poder limpiar después
# ─────────────────────────────────────────────────

ID_ADMIN     = uuid.UUID("aaaaaaaa-0001-0001-0001-000000000001")
ID_PASAJERO  = uuid.UUID("bbbbbbbb-0001-0001-0001-000000000001")
ID_COND_1    = uuid.UUID("cccccccc-0001-0001-0001-000000000001")
ID_COND_2    = uuid.UUID("cccccccc-0002-0002-0002-000000000002")
ID_COND_3    = uuid.UUID("cccccccc-0003-0003-0003-000000000003")

ID_PASAJERO_PERFIL = uuid.UUID("dddddddd-0001-0001-0001-000000000001")
ID_COND_1_PERFIL   = uuid.UUID("eeeeeeee-0001-0001-0001-000000000001")
ID_COND_2_PERFIL   = uuid.UUID("eeeeeeee-0002-0002-0002-000000000002")
ID_COND_3_PERFIL   = uuid.UUID("eeeeeeee-0003-0003-0003-000000000003")

ID_VEH_1 = uuid.UUID("ffffffff-0001-0001-0001-000000000001")
ID_VEH_2 = uuid.UUID("ffffffff-0002-0002-0002-000000000002")
ID_VEH_3 = uuid.UUID("ffffffff-0003-0003-0003-000000000003")

ID_VIAJE_1 = uuid.UUID("11111111-0001-0001-0001-000000000001")
ID_VIAJE_2 = uuid.UUID("11111111-0002-0002-0002-000000000002")

TODOS_LOS_IDS = {
    "usuarios": [ID_ADMIN, ID_PASAJERO, ID_COND_1, ID_COND_2, ID_COND_3],
    "pasajeros": [ID_PASAJERO_PERFIL],
    "conductores": [ID_COND_1_PERFIL, ID_COND_2_PERFIL, ID_COND_3_PERFIL],
    "vehiculos": [ID_VEH_1, ID_VEH_2, ID_VEH_3],
    "viajes": [ID_VIAJE_1, ID_VIAJE_2],
}


# ─────────────────────────────────────────────────
# Insertar datos
# ─────────────────────────────────────────────────

def insertar():
    db = SessionLocal()
    try:
        print("\n📦 Insertando datos de prueba en Supabase...\n")

        # ── Usuarios ──────────────────────────────
        usuarios = [
            Usuario(
                id_usuario=ID_ADMIN,
                uid_firebase="seed-admin-001",
                nombre_completo="Admin Prueba",
                correo="admin.seed@movecare.test",
                telefono="3310000001",
                direccion="Av. Vallarta 1000, Guadalajara",
                discapacidad=None,
                foto_ine="seed",
                foto_ine_reverso="seed",
                foto_perfil="seed",
                rol="administrador",
                activo=True,
                autentificado=True,
            ),
            Usuario(
                id_usuario=ID_PASAJERO,
                uid_firebase="seed-pasajero-001",
                nombre_completo="María García (Prueba)",
                correo="pasajero.seed@movecare.test",
                telefono="3310000002",
                direccion="Calle Juárez 500, Guadalajara",
                discapacidad="motriz",   # ← necesita rampa
                foto_ine="seed",
                foto_ine_reverso="seed",
                foto_perfil="seed",
                rol="pasajero",
                activo=True,
                autentificado=True,
            ),
            Usuario(
                id_usuario=ID_COND_1,
                uid_firebase="seed-conductor-001",
                nombre_completo="Carlos Ramírez (Prueba)",
                correo="conductor1.seed@movecare.test",
                telefono="3310000003",
                direccion="Av. López Mateos 200, Guadalajara",
                discapacidad=None,
                foto_ine="seed",
                foto_ine_reverso="seed",
                foto_perfil="seed",
                rol="conductor",
                activo=True,
                autentificado=True,
            ),
            Usuario(
                id_usuario=ID_COND_2,
                uid_firebase="seed-conductor-002",
                nombre_completo="Mario López (Prueba)",
                correo="conductor2.seed@movecare.test",
                telefono="3310000004",
                direccion="Av. Patria 300, Zapopan",
                discapacidad=None,
                foto_ine="seed",
                foto_ine_reverso="seed",
                foto_perfil="seed",
                rol="conductor",
                activo=True,
                autentificado=True,
            ),
            Usuario(
                id_usuario=ID_COND_3,
                uid_firebase="seed-conductor-003",
                nombre_completo="Ana Torres (Prueba)",
                correo="conductor3.seed@movecare.test",
                telefono="3310000005",
                direccion="Calle Reforma 100, Tlaquepaque",
                discapacidad=None,
                foto_ine="seed",
                foto_ine_reverso="seed",
                foto_perfil="seed",
                rol="conductor",
                activo=True,
                autentificado=True,
            ),
        ]
        for u in usuarios:
            db.merge(u)
        print("  ✓ 5 usuarios creados (1 admin, 1 pasajero, 3 conductores)")

        # ── Pasajero ──────────────────────────────
        pasajero = Pasajero(
            id_pasajero=ID_PASAJERO_PERFIL,
            id_usuario=ID_PASAJERO,
        )
        db.merge(pasajero)
        print("  ✓ Perfil de pasajero creado")

        # ── Conductores ───────────────────────────
        conductores = [
            Conductor(id_conductor=ID_COND_1_PERFIL, id_usuario=ID_COND_1, licencia_conduccion="seed-lic-001"),
            Conductor(id_conductor=ID_COND_2_PERFIL, id_usuario=ID_COND_2, licencia_conduccion="seed-lic-002"),
            Conductor(id_conductor=ID_COND_3_PERFIL, id_usuario=ID_COND_3, licencia_conduccion="seed-lic-003"),
        ]
        for c in conductores:
            db.merge(c)
        print("  ✓ 3 perfiles de conductor creados")

        # ── Vehículos ─────────────────────────────
        vehiculos = [
            Vehiculos(
                id_vehiculo=ID_VEH_1,
                id_conductor=ID_COND_1_PERFIL,
                marca="Toyota", modelo="Sienna", placas="JAL-001",
                color="Blanco", capacidad=6, activo=True,
                accesorios="rampa hidráulica, anclaje para silla de ruedas",
            ),
            Vehiculos(
                id_vehiculo=ID_VEH_2,
                id_conductor=ID_COND_2_PERFIL,
                marca="Nissan", modelo="Urvan", placas="JAL-002",
                color="Gris", capacidad=8, activo=True,
                accesorios=None,   # ← sin accesorios de accesibilidad
            ),
            Vehiculos(
                id_vehiculo=ID_VEH_3,
                id_conductor=ID_COND_3_PERFIL,
                marca="Honda", modelo="Odyssey", placas="JAL-003",
                color="Azul", capacidad=7, activo=True,
                accesorios="rampa manual, cinturón especial",
            ),
        ]
        for v in vehiculos:
            db.merge(v)
        print("  ✓ 3 vehículos creados (C1: rampa hidráulica | C2: sin accesorios | C3: rampa manual)")

        # ── Ubicaciones GPS (Guadalajara) ─────────
        # Conductor 1: cerca del Centro (~2 km del pasajero)
        # Conductor 2: en Zapopan (~8 km)
        # Conductor 3: sin ubicación registrada
        ubicaciones = [
            UbicacionConductor(
                id_conductor=ID_COND_1_PERFIL,
                latitud=20.6720, longitud=-103.3470,   # Zona Centro GDL
            ),
            UbicacionConductor(
                id_conductor=ID_COND_2_PERFIL,
                latitud=20.7200, longitud=-103.3900,   # Zapopan
            ),
        ]
        for ub in ubicaciones:
            existing = db.query(UbicacionConductor).filter(
                UbicacionConductor.id_conductor == ub.id_conductor
            ).first()
            if existing:
                existing.latitud = ub.latitud
                existing.longitud = ub.longitud
            else:
                db.add(ub)
        print("  ✓ 2 ubicaciones GPS registradas (C3 sin ubicación — prueba de robustez)")

        # ── Viajes Pendientes ─────────────────────
        viajes = [
            Viaje(
                id_viaje=ID_VIAJE_1,
                id_pasajero=ID_PASAJERO_PERFIL,
                id_conductor=None,           # ← sin asignar
                punto_inicio="Calle Juárez 500, Guadalajara",
                destino="Hospital Civil, Guadalajara",
                fecha_hora_inicio=datetime(2026, 3, 10, 9, 0),
                metodo_pago="efectivo",
                costo=150.00,
                estado="Pendiente",
                especificaciones="Pasajera usa silla de ruedas, requiere apoyo al subir",
                check_acompanante=True,
                ruta={
                    "inicio": {"lat": 20.6597, "lon": -103.3496},
                    "destino": {"lat": 20.6720, "lon": -103.3380}
                },
            ),
            Viaje(
                id_viaje=ID_VIAJE_2,
                id_pasajero=ID_PASAJERO_PERFIL,
                id_conductor=None,           # ← sin asignar
                punto_inicio="Calle Juárez 500, Guadalajara",
                destino="Plaza del Sol, Guadalajara",
                fecha_hora_inicio=datetime(2026, 3, 11, 14, 0),
                metodo_pago="tarjeta",
                costo=120.00,
                estado="Pendiente",
                especificaciones=None,
                check_acompanante=False,
                ruta={
                    "inicio": {"lat": 20.6597, "lon": -103.3496},
                    "destino": {"lat": 20.6480, "lon": -103.4100}
                },
            ),
        ]
        for viaje in viajes:
            db.merge(viaje)
        print("  ✓ 2 viajes en estado Pendiente creados\n")

        db.commit()
        print("=" * 50)
        print("  DATOS INSERTADOS CORRECTAMENTE")
        print("=" * 50)
        print("""
  Ahora puedes probar en Swagger (http://127.0.0.1:8000/docs):

  1. GET  /ia/conductores/disponibles
     → Debe mostrar 3 conductores disponibles

  2. POST /ia/viajes/asignar  (body: {})
     → La IA asignará el mejor conductor a cada viaje

  Resultado esperado:
     Viaje 1 (pasajera con silla de ruedas)
       → Carlos Ramírez (rampa hidráulica, cerca)

     Viaje 2 (sin necesidad especial)
       → Mario López o Ana Torres (el más cercano)
""")

    except Exception as e:
        db.rollback()
        print(f"\n  ERROR: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()


# ─────────────────────────────────────────────────
# Limpiar datos de prueba
# ─────────────────────────────────────────────────

def limpiar():
    db = SessionLocal()
    try:
        print("\n🗑️  Limpiando datos de prueba...\n")

        for id_v in TODOS_LOS_IDS["viajes"]:
            db.query(Viaje).filter(Viaje.id_viaje == id_v).delete()

        for id_c in TODOS_LOS_IDS["conductores"]:
            db.query(UbicacionConductor).filter(UbicacionConductor.id_conductor == id_c).delete()
            db.query(Vehiculos).filter(Vehiculos.id_conductor == id_c).delete()
            db.query(Conductor).filter(Conductor.id_conductor == id_c).delete()

        for id_p in TODOS_LOS_IDS["pasajeros"]:
            db.query(Pasajero).filter(Pasajero.id_pasajero == id_p).delete()

        for id_u in TODOS_LOS_IDS["usuarios"]:
            db.query(Usuario).filter(Usuario.id_usuario == id_u).delete()

        db.commit()
        print("  ✓ Todos los datos de prueba eliminados\n")

    except Exception as e:
        db.rollback()
        print(f"\n  ERROR al limpiar: {e}")
    finally:
        db.close()


# ─────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limpiar", action="store_true", help="Elimina los datos de prueba")
    args = parser.parse_args()

    if args.limpiar:
        limpiar()
    else:
        insertar()
