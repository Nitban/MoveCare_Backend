from sqlalchemy import Column, Text, TIMESTAMP, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid

class MensajeChat(Base):
    __tablename__ = "mensajes_chat"

    id_mensaje = Column(Integer, primary_key=True, autoincrement=True)
    id_viaje = Column(
        UUID(as_uuid=True),
        ForeignKey("viaje.id_viaje", ondelete="CASCADE"),
        nullable=False
    )
    id_emisor = Column(
        UUID(as_uuid=True),
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False
    )
    contenido = Column(Text, nullable=False)
    fecha_envio = Column(TIMESTAMP, server_default=func.now())

    # Relaciones para acceder fácilmente a los objetos si se necesita
    viaje = relationship("Viaje", backref="mensajes")
    emisor = relationship("Usuario")