from pydantic import BaseModel, UUID4
from datetime import datetime

# Schema para cuando el frontend envía un mensaje
class MensajeCreate(BaseModel):
    id_viaje: UUID4
    contenido: str

# Schema para devolver los mensajes al frontend
class MensajeResponse(BaseModel):
    id_mensaje: int
    id_viaje: UUID4
    id_emisor: UUID4
    contenido: str
    fecha_envio: datetime

    class Config:
        from_attributes = True  # Permite que Pydantic lea el objeto de SQLAlchemy