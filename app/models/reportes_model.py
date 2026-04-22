from sqlalchemy import Column, String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid


class Reporte(Base):
    __tablename__ = "reportes"

    id_reporte = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    id_reportante = Column(UUID(as_uuid=True), nullable=False)
    id_reportado = Column(UUID(as_uuid=True), nullable=False)

    # Llave foránea solo con Administrador (puede ser nulo al crear el reporte)
    id_admin = Column(UUID(as_uuid=True), ForeignKey("administrador.id_administrador"), nullable=True)
    id_viaje = Column(UUID(as_uuid=True), ForeignKey("viaje.id_viaje"), nullable=True)

    tipo_reporte = Column(String, nullable=False)
    descripcion = Column(String, nullable=False)
    estado = Column(String, default="pendiente", nullable=False)
    fecha_reporte = Column(DateTime(timezone=True), server_default=func.now())
    motivo_rechazo = Column(String, nullable=False)

    # Relación en SQLAlchemy (opcional, pero útil si haces consultas cruzadas)
    administrador = relationship("Administrador", back_populates="reporte")
    viaje = relationship("Viaje",back_populates="reporte" )