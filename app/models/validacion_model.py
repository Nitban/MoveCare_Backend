from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid
from app.core.database import Base

class ValidacionUsuario(Base):
    __tablename__ = "validacion_usuario"

    id_validacion = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False)
    estado_validacion = Column(String, default="Pendiente")
    motivo_rechazo = Column(Text, nullable=True)
    fecha_revision = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    ine_frente = Column(Text, nullable=False)
    ine_reverso = Column(Text, nullable=False)