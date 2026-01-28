from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime


class CrearViajeSchema(BaseModel):
    punto_inicio: str
    destino: str
    fecha_hora_inicio: datetime
    metodo_pago: str
    costo: Optional[float] = None
    ruta: Optional[Dict] = None
    duracion_estimada: Optional[int] = None
    cal_pasajero: Optional[float] = 5.0
    cal_conductor: Optional[float] = 5.0
    especificaciones = Optional[str] = None
    check_acompanante = Optional[bool] = None
