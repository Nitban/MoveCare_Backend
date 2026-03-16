"""
Seed de datos para demo en vivo del módulo de métricas (Módulo 3 IA)

Inserta viajes históricos variados para el conductor de prueba (Carlos Ramírez)
con distintos estados, fechas, costos, duraciones y rutas reales.

Uso:
  python seed_metricas.py          → inserta datos
  python seed_metricas.py --limpiar → elimina solo los viajes de métricas
"""

import sys, os, uuid, argparse
from datetime import datetime, timedelta
import random

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from app.core.database import SessionLocal
from app.models.viaje_model import Viaje

# ─── IDs del seed_prueba.py (conductor Carlos Ramírez) ───────────────────────
ID_COND_1_PERFIL   = uuid.UUID("eeeeeeee-0001-0001-0001-000000000001")
ID_PASAJERO_PERFIL = uuid.UUID("dddddddd-0001-0001-0001-000000000001")

# IDs fijos para poder limpiar
VIAJE_IDS = [uuid.UUID(f"99999999-{str(i).zfill(4)}-0000-0000-000000000001") for i in range(1, 31)]

# ─── Datos de ejemplo ─────────────────────────────────────────────────────────
RUTAS = [
    {"origen": "Guadalajara Centro", "destino": "Hospital Civil", "km": 3.2, "min": 18},
    {"origen": "Zapopan Centro",     "destino": "Plaza Andares",  "km": 5.8, "min": 25},
    {"origen": "Providencia",        "destino": "Expo GDL",       "km": 7.1, "min": 32},
    {"origen": "Tlaquepaque",        "destino": "Estadio Jalisco","km": 9.4, "min": 40},
    {"origen": "Chapalita",          "destino": "Mercado San Juan","km": 4.5,"min": 22},
    {"origen": "Colonia Americana",  "destino": "Plaza del Sol",  "km": 6.3, "min": 28},
]

def insertar():
    db = SessionLocal()
    try:
        print("\n📊 Insertando datos de métricas de prueba...\n")

        hoy = datetime.now()
        viajes_insertados = 0

        for i, vid in enumerate(VIAJE_IDS):
            # Distribuir en los últimos 30 días
            dias_atras = i % 30
            hora = random.choice([8, 9, 10, 11, 14, 15, 16, 17, 18])
            fecha = (hoy - timedelta(days=dias_atras)).replace(
                hour=hora, minute=random.randint(0, 59), second=0, microsecond=0
            )

            ruta_data = RUTAS[i % len(RUTAS)]

            # Distribuir estados: ~70% finalizado, ~20% cancelado, ~10% en_curso
            if i < 21:
                estado = "finalizado"
                fecha_fin = fecha + timedelta(minutes=ruta_data["min"] + random.randint(-5, 10))
                duracion_real = ruta_data["min"] + random.randint(-3, 8)
                cal = round(random.uniform(3.5, 5.0), 1)
            elif i < 27:
                estado = "cancelado"
                fecha_fin = None
                duracion_real = None
                cal = None
            else:
                estado = "en_curso"
                fecha_fin = None
                duracion_real = None
                cal = None

            costo = round(ruta_data["km"] * random.uniform(14, 18), 2)

            viaje = Viaje(
                id_viaje=vid,
                id_pasajero=ID_PASAJERO_PERFIL,
                id_conductor=ID_COND_1_PERFIL,
                punto_inicio=ruta_data["origen"],
                destino=ruta_data["destino"],
                fecha_hora_inicio=fecha,
                fecha_hora_fin=fecha_fin,
                metodo_pago=random.choice(["efectivo", "tarjeta"]),
                costo=costo,
                estado=estado,
                duracion_estimada=ruta_data["min"],
                duracion_real=duracion_real,
                cal_conductor=cal,
                especificaciones=None,
                check_acompanante=False,
                check_destinos=False,
                ruta={
                    "distancia_km": ruta_data["km"],
                    "duracion_estimada_min": ruta_data["min"],
                    "origen": {"direccion": ruta_data["origen"]},
                    "destino": {"direccion": ruta_data["destino"]},
                },
            )
            db.merge(viaje)
            viajes_insertados += 1

        db.commit()

        finalizados = sum(1 for i in range(30) if i < 21)
        cancelados  = sum(1 for i in range(30) if 21 <= i < 27)
        en_curso    = sum(1 for i in range(30) if i >= 27)

        print(f"  ✓ {viajes_insertados} viajes insertados para Carlos Ramírez")
        print(f"     → {finalizados} finalizados  |  {cancelados} cancelados  |  {en_curso} en curso")
        print(f"     → Distribuidos en los últimos 30 días\n")
        print("=" * 55)
        print("  DEMO LISTO — prueba en Swagger o en la app:")
        print("=" * 55)
        print("""
  Opción A — Swagger (sin login):
    GET http://127.0.0.1:8000/ia/demo/metricas
    → Métricas del conductor de prueba sin autenticación

  Opción B — Swagger (con token de conductor):
    1. POST /auth/login  con conductor1.seed@movecare.test
    2. Copiar el token → Authorize en Swagger
    3. GET /ia/reportes/conductor
    → Métricas reales del conductor autenticado

  Opción C — Flutter app:
    Iniciar sesión como conductor1.seed@movecare.test
    Ir a: Mis Métricas (tab 2 del menú conductor)
""")

    except Exception as e:
        db.rollback()
        print(f"\n  ERROR: {e}")
        import traceback; traceback.print_exc()
    finally:
        db.close()


def limpiar():
    db = SessionLocal()
    try:
        print("\n🗑️  Limpiando viajes de métricas de prueba...\n")
        for vid in VIAJE_IDS:
            db.query(Viaje).filter(Viaje.id_viaje == vid).delete()
        db.commit()
        print("  ✓ Viajes de métricas eliminados\n")
    except Exception as e:
        db.rollback()
        print(f"\n  ERROR al limpiar: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--limpiar", action="store_true")
    args = parser.parse_args()
    limpiar() if args.limpiar else insertar()
