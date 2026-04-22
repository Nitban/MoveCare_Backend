from sqlalchemy import Column, Float, Text, TIMESTAMP, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class CargaGasolina(Base):
    __tablename__ = "carga_gasolina"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_conductor = Column(
        UUID(as_uuid=True),
        ForeignKey("conductor.id_conductor", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Litros en el tanque DESPUÉS de cargar (ej. 45 de 50)
    litros_en_tanque = Column(Float, nullable=False)
    capacidad_tanque  = Column(Float, nullable=False, default=50.0)
    rendimiento_kmL   = Column(Float, nullable=False, default=10.0)
    costo             = Column(Float, nullable=False)
    # Km totales del conductor al momento de registrar la carga
    km_al_cargar      = Column(Float, nullable=False, default=0.0)
    notas             = Column(Text, nullable=True)
    fecha             = Column(TIMESTAMP(timezone=True), server_default=func.now())

    conductor = relationship("Conductor", backref="cargas_gasolina")
