from sqlalchemy import Column, Text, String, TIMESTAMP, ForeignKey, Integer, Numeric
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
import uuid

from app.core.database import Base


class Viaje(Base):
    __tablename__ = "viaje"

    id_viaje = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )

    id_pasajero = Column(
        UUID(as_uuid=True),
        ForeignKey("pasajero.id_pasajero", ondelete="SET NULL"),
        nullable=True
    )

    id_conductor = Column(
        UUID(as_uuid=True),
        ForeignKey("conductor.id_conductor", ondelete="SET NULL"),
        nullable=True
    )

    punto_inicio = Column(Text, nullable=False)
    destino = Column(Text, nullable=False)

    fecha_hora_inicio = Column(
        TIMESTAMP,
        server_default=func.now()
    )

    fecha_hora_fin = Column(TIMESTAMP, nullable=True)

    metodo_pago = Column(String, nullable=True)
    costo = Column(Numeric(10, 2), nullable=True)

    estado = Column(
        String,
        nullable=False,
        default="pendiente"
        # pendiente | en_curso | finalizado | cancelado
    )

    ruta = Column(JSONB, nullable=True)

    duracion_estimada = Column(Integer, nullable=True)
    duracion_real = Column(Integer, nullable=True)
