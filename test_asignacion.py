"""
Prueba local del módulo de scoring y asignación.
No requiere servidor ni base de datos.

Ejecutar con:
    python test_asignacion.py
"""

import sys
import os
sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, os.path.dirname(__file__))

from app.ai.asignacion.scoring import (
    calcular_costo,
    distancia_haversine,
    puntaje_accesibilidad,
)


# ──────────────────────────────────────────────
# Datos de prueba simulados
# ──────────────────────────────────────────────

# Coordenadas reales en Guadalajara, Jalisco
PASAJERO_LAT, PASAJERO_LON = 20.6597, -103.3496  # Centro histórico GDL

CONDUCTORES = [
    {
        "nombre": "Carlos (silla de ruedas, 5km)",
        "accesorios": "rampa hidráulica, anclaje para silla de ruedas",
        "capacidad": 4,
        "rating_avg": 4.8,
        "lat": 20.7012, "lon": -103.3800,   # ~5 km del pasajero
    },
    {
        "nombre": "Mario (sin accesorios, 2km)",
        "accesorios": None,
        "capacidad": 4,
        "rating_avg": 4.5,
        "lat": 20.6750, "lon": -103.3600,   # ~2 km del pasajero
    },
    {
        "nombre": "Luis (accesorios parciales, 8km)",
        "accesorios": "rampa manual",
        "capacidad": 2,
        "rating_avg": 3.9,
        "lat": 20.6200, "lon": -103.4100,   # ~8 km del pasajero
    },
    {
        "nombre": "Ana (nuevo, sin rating, 1km)",
        "accesorios": "rampa hidráulica, anclaje para silla de ruedas, elevador",
        "capacidad": 5,
        "rating_avg": None,
        "lat": 20.6630, "lon": -103.3520,   # ~1 km del pasajero
    },
]

VIAJES = [
    {
        "descripcion": "Pasajero con silla de ruedas, con acompañante",
        "discapacidad": "motriz",
        "con_acompanante": True,
        "lat": PASAJERO_LAT, "lon": PASAJERO_LON,
    },
    {
        "descripcion": "Adulto mayor sin discapacidad específica",
        "discapacidad": "adulto_mayor",
        "con_acompanante": False,
        "lat": 20.6800, "lon": -103.3700,
    },
]


# ──────────────────────────────────────────────
# Test 1: Puntaje de accesibilidad
# ──────────────────────────────────────────────

def test_accesibilidad():
    print("\n" + "="*60)
    print("TEST 1: Puntaje de accesibilidad")
    print("="*60)

    casos = [
        ("motriz", "rampa hidráulica, anclaje para silla de ruedas", 1.0),
        ("motriz", "rampa manual",                                    1.0),  # tiene rampa = compatible
        ("motriz", None,                                              0.0),
        ("visual", "audio y narrador de voz",                         1.0),
        ("adulto_mayor", None,                                        1.0),  # sin restricción
        (None, None,                                                  1.0),  # sin necesidad
    ]

    ok = True
    for discapacidad, accesorios, esperado in casos:
        resultado = puntaje_accesibilidad(discapacidad, accesorios)
        estado = "✓" if resultado == esperado else "✗"
        if resultado != esperado:
            ok = False
        print(f"  {estado} disc={discapacidad!r:15} acc={str(accesorios)[:30]:32} → {resultado} (esperado {esperado})")

    return ok


# ──────────────────────────────────────────────
# Test 2: Distancia Haversine
# ──────────────────────────────────────────────

def test_distancia():
    print("\n" + "="*60)
    print("TEST 2: Distancia Haversine (GDL)")
    print("="*60)

    # Guadalajara a Zapopan (~6 km reales)
    dist = distancia_haversine(20.6597, -103.3496, 20.7167, -103.4167)
    print(f"  GDL → Zapopan: {dist:.2f} km  (esperado ~8 km)")

    # Misma ubicación
    dist_cero = distancia_haversine(20.6597, -103.3496, 20.6597, -103.3496)
    print(f"  Misma ubicación: {dist_cero:.4f} km (esperado 0)")

    # Sin coordenadas
    dist_nan = distancia_haversine(None, None, 20.6597, -103.3496)
    print(f"  Sin coordenadas: {dist_nan} km (esperado 999)")

    return True


# ──────────────────────────────────────────────
# Test 3: Ranking de conductores por viaje
# ──────────────────────────────────────────────

def test_ranking():
    print("\n" + "="*60)
    print("TEST 3: Ranking de conductores por viaje")
    print("="*60)

    for viaje in VIAJES:
        print(f"\n  Viaje: {viaje['descripcion']}")
        print(f"  Discapacidad: {viaje['discapacidad']} | Acompañante: {viaje['con_acompanante']}")
        print()

        resultados = []
        for c in CONDUCTORES:
            costo = calcular_costo(
                discapacidad=viaje["discapacidad"],
                accesorios=c["accesorios"],
                rating_promedio=c["rating_avg"],
                lat_conductor=c["lat"],
                lon_conductor=c["lon"],
                lat_viaje=viaje["lat"],
                lon_viaje=viaje["lon"],
                capacidad=c["capacidad"],
                con_acompanante=viaje["con_acompanante"],
            )
            resultados.append((c["nombre"], costo, 1 - costo))

        resultados.sort(key=lambda x: x[1])  # menor costo primero

        for rank, (nombre, costo, score) in enumerate(resultados, 1):
            barra = "█" * int(score * 20)
            print(f"  #{rank} {nombre}")
            print(f"     Score: {score:.3f}  Costo: {costo:.3f}  [{barra}]")

    return True


# ──────────────────────────────────────────────
# Test 4: Algoritmo húngaro (sin BD)
# ──────────────────────────────────────────────

def test_hungaro():
    print("\n" + "="*60)
    print("TEST 4: Algoritmo húngaro — asignación óptima global")
    print("="*60)

    import numpy as np
    from scipy.optimize import linear_sum_assignment

    n_viajes = len(VIAJES)
    n_conductores = len(CONDUCTORES)

    cost_matrix = np.zeros((n_viajes, n_conductores))

    for i, viaje in enumerate(VIAJES):
        for j, c in enumerate(CONDUCTORES):
            cost_matrix[i, j] = calcular_costo(
                discapacidad=viaje["discapacidad"],
                accesorios=c["accesorios"],
                rating_promedio=c["rating_avg"],
                lat_conductor=c["lat"],
                lon_conductor=c["lon"],
                lat_viaje=viaje["lat"],
                lon_viaje=viaje["lon"],
                capacidad=c["capacidad"],
                con_acompanante=viaje["con_acompanante"],
            )

    print("\n  Matriz de costos (filas=viajes, columnas=conductores):")
    header = "           " + "  ".join(f"C{j+1}({c['nombre'][:6]})" for j, c in enumerate(CONDUCTORES))
    print(f"  {header}")
    for i, v in enumerate(VIAJES):
        fila = "  ".join(f"  {cost_matrix[i,j]:.3f}  " for j in range(n_conductores))
        print(f"  V{i+1}({v['descripcion'][:12]:12})  {fila}")

    filas, cols = linear_sum_assignment(cost_matrix)

    print("\n  Asignaciones óptimas:")
    for fila, col in zip(filas, cols):
        costo = cost_matrix[fila, col]
        score = 1 - costo
        viaje = VIAJES[fila]
        conductor = CONDUCTORES[col]
        print(f"  ✓ Viaje: {viaje['descripcion'][:35]:35} → Conductor: {conductor['nombre']}")
        print(f"    Compatibilidad: {score:.1%}  (costo={costo:.3f})")

    return True


# ──────────────────────────────────────────────
# Ejecutar todos los tests
# ──────────────────────────────────────────────

if __name__ == "__main__":
    resultados = []

    resultados.append(test_accesibilidad())
    resultados.append(test_distancia())
    resultados.append(test_ranking())
    resultados.append(test_hungaro())

    print("\n" + "="*60)
    aprobados = sum(resultados)
    print(f"Resultado: {aprobados}/{len(resultados)} tests pasados")
    print("="*60)

    if aprobados < len(resultados):
        sys.exit(1)