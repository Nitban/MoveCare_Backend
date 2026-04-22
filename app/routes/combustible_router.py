"""
Router de Control de Combustible — MoveCare

Endpoints:
  POST /combustible/registrar   → Registrar una carga de gasolina
  GET  /combustible/historial   → Historial de cargas del conductor
  GET  /combustible/nivel       → Nivel estimado actual basado en km recorridos
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.dependencies.auth_dependencies import require_conductor
from app.models.combustible_model import CargaGasolina
from app.models.conductor_model import Conductor

router = APIRouter(prefix="/combustible", tags=["Combustible"])


# ─────────────────────────────────────────────
# Schemas
# ─────────────────────────────────────────────

class RegistrarCargaPayload(BaseModel):
    litros_en_tanque: float = Field(..., gt=0, description="Litros en tanque después de cargar")
    capacidad_tanque: float = Field(50.0, gt=0, description="Capacidad total del tanque en litros")
    rendimiento_kmL:  float = Field(10.0, gt=0, description="Rendimiento esperado en km/L")
    costo:            float = Field(..., ge=0, description="Costo pagado en esta carga")
    km_al_cargar:     float = Field(0.0,  ge=0, description="Km totales del conductor al momento de cargar")
    notas: Optional[str]   = Field(None,  max_length=300)


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def _id_conductor(user: dict, db: Session) -> str:
    conductor = db.query(Conductor).filter(
        Conductor.id_usuario == user["id_usuario"]
    ).first()
    if not conductor:
        raise HTTPException(status_code=404, detail="Conductor no encontrado")
    return conductor.id_conductor


def _calcular_nivel(carga: CargaGasolina, km_actuales: float) -> dict:
    km_desde_carga   = max(0.0, km_actuales - carga.km_al_cargar)
    litros_gastados  = km_desde_carga / carga.rendimiento_kmL
    litros_actuales  = max(0.0, carga.litros_en_tanque - litros_gastados)
    nivel            = min(1.0, litros_actuales / carga.capacidad_tanque)
    return {
        "nivel":               round(nivel, 3),
        "porcentaje":          round(nivel * 100, 1),
        "litros_actuales":     round(litros_actuales, 1),
        "capacidad_tanque":    carga.capacidad_tanque,
        "km_desde_carga":      round(km_desde_carga, 1),
        "rendimiento_kmL":     carga.rendimiento_kmL,
        "ultima_carga_fecha":  carga.fecha.isoformat() if carga.fecha else None,
        "ultima_carga_litros": carga.litros_en_tanque,
        "ultima_carga_costo":  carga.costo,
    }


# ─────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────

@router.post(
    "/registrar",
    summary="Registrar una carga de gasolina",
)
def registrar_carga(
    payload: RegistrarCargaPayload,
    user=Depends(require_conductor),
    db: Session = Depends(get_db),
):
    """
    El conductor registra cuánta gasolina cargó, el costo y los km actuales.
    El sistema guardará esta carga y la usará para estimar el nivel actual.

    - **litros_en_tanque**: litros que quedaron en el tanque DESPUÉS de cargar
    - **km_al_cargar**: km totales del conductor al momento del registro (viene del endpoint /ia/reportes/conductor)
    """
    id_cond = _id_conductor(user, db)

    carga = CargaGasolina(
        id_conductor     = id_cond,
        litros_en_tanque = payload.litros_en_tanque,
        capacidad_tanque = payload.capacidad_tanque,
        rendimiento_kmL  = payload.rendimiento_kmL,
        costo            = payload.costo,
        km_al_cargar     = payload.km_al_cargar,
        notas            = payload.notas,
    )
    db.add(carga)
    db.commit()
    db.refresh(carga)

    return {
        "ok":      True,
        "mensaje": "Carga de gasolina registrada",
        "id":      str(carga.id),
        "fecha":   carga.fecha.isoformat(),
    }


@router.get(
    "/historial",
    summary="Historial de cargas de gasolina del conductor",
)
def historial_cargas(
    limite: int = Query(10, ge=1, le=50),
    user=Depends(require_conductor),
    db: Session = Depends(get_db),
):
    """
    Devuelve las últimas cargas de gasolina del conductor, ordenadas de más reciente a más antigua.
    """
    id_cond = _id_conductor(user, db)

    cargas = (
        db.query(CargaGasolina)
        .filter(CargaGasolina.id_conductor == id_cond)
        .order_by(CargaGasolina.fecha.desc())
        .limit(limite)
        .all()
    )

    return {
        "ok":     True,
        "total":  len(cargas),
        "cargas": [
            {
                "id":               str(c.id),
                "litros_en_tanque": c.litros_en_tanque,
                "capacidad_tanque": c.capacidad_tanque,
                "rendimiento_kmL":  c.rendimiento_kmL,
                "costo":            c.costo,
                "km_al_cargar":     c.km_al_cargar,
                "notas":            c.notas,
                "fecha":            c.fecha.isoformat() if c.fecha else None,
            }
            for c in cargas
        ],
    }


@router.get(
    "/nivel",
    summary="Nivel estimado de gasolina del conductor",
)
def nivel_combustible(
    km_actuales: float = Query(0.0, ge=0, description="Km totales actuales del conductor"),
    user=Depends(require_conductor),
    db: Session = Depends(get_db),
):
    """
    Calcula el nivel estimado de gasolina basado en la última carga registrada
    y los km recorridos desde entonces.

    **Fórmula:**
    ```
    litros_gastados = (km_actuales - km_al_cargar) / rendimiento_kmL
    litros_actuales = litros_en_tanque - litros_gastados
    nivel           = litros_actuales / capacidad_tanque
    ```

    Pasar `km_actuales` desde el KPI de km_totales del endpoint /ia/reportes/conductor.
    """
    id_cond = _id_conductor(user, db)

    ultima = (
        db.query(CargaGasolina)
        .filter(CargaGasolina.id_conductor == id_cond)
        .order_by(CargaGasolina.fecha.desc())
        .first()
    )

    if not ultima:
        return {
            "ok":              True,
            "sin_registros":   True,
            "nivel":           None,
            "mensaje":         "Sin cargas registradas — registra tu primera carga de gasolina",
        }

    return {"ok": True, "sin_registros": False, **_calcular_nivel(ultima, km_actuales)}
