from sqlalchemy import Column, Float, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
import uuid

from app.core.database import Base


class UbicacionConductor(Base):
    __tablename__ = "ubicacion_conductor"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_conductor = Column(
        UUID(as_uuid=True),
        ForeignKey("conductor.id_conductor", ondelete="CASCADE"),
        unique=True,
        nullable=False
    )
    latitud = Column(Float, nullable=False)
    longitud = Column(Float, nullable=False)
    actualizado_en = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now())

    conductor = relationship("Conductor", backref="ubicacion")
