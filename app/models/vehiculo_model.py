# app/models/vehiculo_model.py
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship, backref # <--- Importa backref
import uuid
from app.core.database import Base

class Vehiculos(Base):
    __tablename__ = "vehiculos"

    id_vehiculo = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_conductor = Column(
        UUID(as_uuid=True),
        ForeignKey("conductor.id_conductor", ondelete="CASCADE"),
        nullable=False
    )

    marca = Column(String, nullable=False)
    modelo = Column(String, nullable=False)
    placas = Column(String, nullable=False)
    color = Column(String, nullable=True)
    capacidad = Column(Integer, nullable=True)
    activo = Column(Boolean, default=True)
    accesorios = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now())

    # CAMBIO AQUÍ: Usamos backref en lugar de back_populates
    conductor = relationship(
        "Conductor",
        backref=backref("vehiculos", cascade="all, delete-orphan") 
    )