from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime
from uuid import UUID

class DestinoItem(BaseModel):
    direccion: str = None
    lat: Optional[float] = None
    lng: Optional[float] = None
    orden: Optional[int] = None

class CrearViajeSchema(BaseModel):
    punto_inicio: str
    destino: Optional[str] = None
    fecha_hora_inicio: datetime
    metodo_pago: str
    costo: Optional[float] = None
    ruta: Optional[Dict] = None
    duracion_estimada: Optional[int] = None
    cal_pasajero: Optional[float] = 5.0
    cal_conductor: Optional[float] = 5.0
    especificaciones: Optional[str] = None
    check_acompanante: Optional[bool] = None
    id_acompanante: Optional[str] = None
    check_destinos: bool = True
    destinos: List[DestinoItem] = None

class ViajeDetalleResponse(BaseModel):
    id_viaje: UUID
    fecha_inicio: str  # Formato: "DD/MM/YYYY"
    punto_inicio: str
    destino: Optional[str]
    estado: str
    nombre_conductor: Optional[str] = "Pendiente"
    foto_conductor: Optional[str] = None
    # calificacion_conductor: Optional[float] = None # Próximamente

    class Config:
        from_attributes = True


