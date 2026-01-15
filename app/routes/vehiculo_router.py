from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.vehiculos import VehiculoCreate, VehiculoResponse
from app.services.vehiculo_service import VehiculoService

router = APIRouter(
    prefix="/vehiculos",
    tags=["Vehiculos"]
)

@router.post("/", response_model=VehiculoResponse)
def registrar_vehiculo(
    data: VehiculoCreate,
    db: Session = Depends(get_db)
):
    try:
        vehiculo = VehiculoService.crear_vehiculo(db, data)
        return vehiculo
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
