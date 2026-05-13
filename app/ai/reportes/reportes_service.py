from sqlalchemy.orm import Session
from app.models.viaje_model import Viaje
from app.models.conductor_model import Conductor
from datetime import datetime, timedelta
import pandas as pd


def _empty_metrics() -> dict:
    return {
        "kpis": {
            "total_viajes": 0,
            "km_totales": 0.0,
            "calificacion": None,
            "ganancias_total": 0.0,
        },
        "viajes_semana": [0, 0, 0, 0, 0, 0, 0],
        "ganancias_semanas": [0.0, 0.0, 0.0, 0.0, 0.0],
        "estados": {"completados": 0.0, "cancelados": 0.0, "en_curso": 0.0},
        "resumen": {
            "viajes_completados": 0,
            "viajes_cancelados": 0,
            "km_promedio": 0.0,
            "tiempo_promedio_min": 0,
            "ganancia_promedio": 0.0,
            "mejor_dia": "N/A",
        },
    }


def _detectar_anomalias(df: pd.DataFrame) -> list:
    anomalias = []

    if len(df) >= 10:
        cals_recientes = df.tail(5)["cal_conductor"].dropna()
        cals_previas = df.iloc[-15:-5]["cal_conductor"].dropna()
        if len(cals_recientes) > 0 and len(cals_previas) > 0:
            caida = float(cals_previas.mean()) - float(cals_recientes.mean())
            if caida > 1.0:
                anomalias.append({
                    "tipo": "caida_rating",
                    "severidad": "alta" if caida > 1.5 else "media",
                    "detalle": f"Rating cayó {round(caida, 1)} estrellas en los últimos 5 viajes",
                })

    estados_recientes = df.tail(10)["estado"]
    tasa_cancelacion = (estados_recientes == "cancelado").sum() / len(estados_recientes)
    if tasa_cancelacion > 0.3:
        anomalias.append({
            "tipo": "cancelaciones_altas",
            "severidad": "alta" if tasa_cancelacion > 0.5 else "media",
            "detalle": f"{round(tasa_cancelacion * 100, 1)}% de cancelaciones en los últimos 10 viajes",
        })

    return anomalias


def obtener_metricas_conductor(db: Session, id_usuario: str) -> dict:
    # Buscar el conductor por id_usuario
    conductor = db.query(Conductor).filter(
        Conductor.id_usuario == id_usuario
    ).first()

    if not conductor:
        return _empty_metrics()

    viajes = db.query(Viaje).filter(
        Viaje.id_conductor == conductor.id_conductor
    ).all()

    if not viajes:
        return _empty_metrics()

    # Construir DataFrame
    registros = []
    for v in viajes:
        distancia = 0.0
        if v.ruta and isinstance(v.ruta, dict):
            distancia = float(v.ruta.get("distancia_km", 0) or 0)
        registros.append({
            "estado": v.estado or "",
            "costo": float(v.costo) if v.costo else 0.0,
            "cal_conductor": float(v.cal_conductor) if v.cal_conductor else None,
            "fecha": v.fecha_hora_inicio,
            "duracion_real": v.duracion_real,
            "duracion_estimada": v.duracion_estimada,
            "distancia_km": distancia,
        })

    df = pd.DataFrame(registros)
    df["fecha"] = pd.to_datetime(df["fecha"])
    df["estado"] = df["estado"].str.lower()

    # ── KPIs ──────────────────────────────────────────────────────────────────
    total_viajes = len(df)
    km_totales = round(float(df["distancia_km"].sum()), 1)

    cals = df["cal_conductor"].dropna()
    calificacion = round(float(cals.mean()), 1) if len(cals) > 0 else None

    ganancias_total = round(float(df["costo"].sum()), 2)

    # ── Viajes por día (semana actual L-D) ────────────────────────────────────
    hoy = datetime.now()
    inicio_semana = hoy - timedelta(days=hoy.weekday())
    inicio_semana = inicio_semana.replace(hour=0, minute=0, second=0, microsecond=0)

    semana_df = df[df["fecha"] >= inicio_semana]
    viajes_semana = []
    for i in range(7):
        dia = (inicio_semana + timedelta(days=i)).date()
        conteo = int((semana_df["fecha"].dt.date == dia).sum())
        viajes_semana.append(conteo)

    # ── Ganancias por semana (mes actual, hasta 5 semanas) ───────────────────
    inicio_mes = hoy.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    mes_df = df[df["fecha"] >= inicio_mes]
    ganancias_semanas = []
    for s in range(5):
        inicio_s = inicio_mes + timedelta(weeks=s)
        fin_s = inicio_s + timedelta(weeks=1)
        ganancia_s = mes_df[
            (mes_df["fecha"] >= inicio_s) & (mes_df["fecha"] < fin_s)
        ]["costo"].sum()
        ganancias_semanas.append(round(float(ganancia_s), 2))

    # ── Estados ───────────────────────────────────────────────────────────────
    estados_count = df["estado"].value_counts()
    pct = lambda estado: round(float(estados_count.get(estado, 0)) / total_viajes * 100, 1)

    completados = pct("finalizado")
    cancelados = pct("cancelado")
    en_curso = pct("en_curso")

    # ── Mejor día de la semana (histórico) ────────────────────────────────────
    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    viajes_por_dia = df.groupby(df["fecha"].dt.dayofweek).size()
    mejor_dia = dias_nombres[int(viajes_por_dia.idxmax())] if len(viajes_por_dia) > 0 else "N/A"

    # ── Tiempo promedio ───────────────────────────────────────────────────────
    duraciones = df["duracion_real"].dropna()
    if len(duraciones) == 0:
        duraciones = df["duracion_estimada"].dropna()
    tiempo_promedio = int(round(float(duraciones.mean()))) if len(duraciones) > 0 else 0

    # ── KM promedio ───────────────────────────────────────────────────────────
    km_promedio = round(float(df["distancia_km"].mean()), 1) if km_totales > 0 else 0.0

    ganancia_promedio = round(ganancias_total / total_viajes, 2) if total_viajes > 0 else 0.0

    # ── Proyección de ganancias ───────────────────────────────────────────────
    proyeccion_7d = None
    proyeccion_30d = None
    tendencia = "sin_datos"

    ganancias_diarias = df.groupby(df["fecha"].dt.date)["costo"].sum()
    if len(ganancias_diarias) >= 3:
        ema = ganancias_diarias.ewm(span=3).mean()
        promedio_reciente = float(ema.iloc[-1])
        proyeccion_7d = round(promedio_reciente * 7, 2)
        proyeccion_30d = round(promedio_reciente * 30, 2)
        tendencia = "creciente" if float(ema.iloc[-1]) > float(ema.iloc[0]) else "decreciente"

    return {
        "kpis": {
            "total_viajes": total_viajes,
            "km_totales": km_totales,
            "calificacion": calificacion,
            "ganancias_total": ganancias_total,
        },
        "viajes_semana": viajes_semana,
        "ganancias_semanas": ganancias_semanas,
        "estados": {
            "completados": completados,
            "cancelados": cancelados,
            "en_curso": en_curso,
        },
        "resumen": {
            "viajes_completados": int(estados_count.get("finalizado", 0)),
            "viajes_cancelados": int(estados_count.get("cancelado", 0)),
            "km_promedio": km_promedio,
            "tiempo_promedio_min": tiempo_promedio,
            "ganancia_promedio": ganancia_promedio,
            "mejor_dia": mejor_dia,
        },
        "proyecciones": {
            "proximos_7_dias": proyeccion_7d,
            "proximos_30_dias": proyeccion_30d,
            "tendencia": tendencia,
        },
        "anomalias": _detectar_anomalias(df),
    }
