from sqlalchemy import Column, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base


class Notificacion(Base):
    __tablename__ = "notificaciones"

    id_notificacion = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False)

    titulo = Column(String, nullable=False)
    mensaje = Column(Text, nullable=False)
    tipo = Column(String, nullable=False)
    leida = Column(Boolean, default=False)

    fecha_creacion = Column(DateTime(timezone=True), server_default=func.now())