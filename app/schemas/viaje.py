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
