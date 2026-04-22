import uuid
from sqlalchemy import Column, String, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
from app.core.database import Base

class Auditoria(Base):
    __tablename__ = "auditoria" # O "auditorias" según como esté creada en tu BD

    id_auditoria = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_admin = Column(UUID(as_uuid=True), ForeignKey("administrador.id_administrador"), nullable=False)
    accion = Column(Text, nullable=False)
    tabla_afectada = Column(String, nullable=False)
    id_objetivo = Column(UUID(as_uuid=True), nullable=True) # Puede ser nulo si la acción es general
    detalle = Column(Text, nullable=True)
    fecha = Column(DateTime, server_default=func.now(), nullable=False)
    ip_origen = Column(INET, nullable=True)