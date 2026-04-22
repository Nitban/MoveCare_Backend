from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.orm import Session
from app.schemas.reportes import ReporteCreate, ReporteResponse, ReporteUpdateEstado
from app.services.reportes_service import ReporteService
from app.core.database import get_db  # Ajusta la ruta a tu dependencia de BD
from typing import List
from app.dependencies.auth_dependencies import require_admin

router = APIRouter(
    prefix="/api/reportes",
    tags=["Reportes"]
)


@router.post("/incidencia", response_model=ReporteResponse, status_code=status.HTTP_201_CREATED)
async def crear_incidencia(
        reporte: ReporteCreate,
        db: Session = Depends(get_db)
):
    try:
        resultado = ReporteService.registrar_incidencia(db, reporte)
        return resultado

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al procesar el reporte: {str(e)}"
        )

@router.get("/pendientes", response_model=List[ReporteResponse], status_code=status.HTTP_200_OK)
async def ver_reportes_pendientes(db: Session = Depends(get_db)):
    """
    Retorna todos los reportes cuyo estado es 'Pendiente'.
    """
    try:
        resultado = ReporteService.obtener_reportes_pendientes(db)
        return resultado
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al obtener los reportes: {str(e)}"
        )


@router.put("/{id_reporte}/estado", response_model=ReporteResponse, status_code=status.HTTP_200_OK)
async def cambiar_estado_reporte(
    id_reporte: str,
    datos_update: ReporteUpdateEstado,
    db: Session = Depends(get_db),
    admin_user: dict = Depends(require_admin)
):
    """
    Actualiza el estado de un reporte a 'Aceptado' o 'Rechazado', registra al administrador
    y guarda el motivo en caso de ser rechazado.
    """
    try:
        resultado = ReporteService.actualizar_estado_reporte(
            db=db,
            id_reporte=id_reporte,
            nuevo_estado=datos_update.estado,
            id_usuario_admin=admin_user["id_usuario"], # 🔥 Corregido para que coincida con el servicio
            motivo_rechazo=datos_update.motivo_rechazo
        )
        return resultado
    except HTTPException as http_e:
        raise http_e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error interno al actualizar el reporte: {str(e)}"
        )