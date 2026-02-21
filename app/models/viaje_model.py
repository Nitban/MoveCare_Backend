from sqlalchemy import Column, Text, String, TIMESTAMP, ForeignKey, Integer, Numeric, Float, Boolean
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
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
        default="Pendiente"
        # pendiente | agendado | en_curso | finalizado | cancelado
    )

    ruta = Column(JSONB, nullable=True)

    duracion_estimada = Column(Integer, nullable=True)
    duracion_real = Column(Integer, nullable=True)
    cal_pasajero = Column(Float, nullable=True)
    cal_conductor = Column(Float, nullable=True)
    especificaciones = Column(String, nullable=True)
    check_acompanante = Column(Boolean, nullable=True)
    id_acompanante = Column(
        UUID(as_uuid=True),
        ForeignKey("acompanante.id_acompanante", ondelete="SET NULL"),
        nullable=True
    )

    check_destinos = Column(
        Boolean,
        nullable=False,
        default=False
    )

    destinos = Column(
        JSONB,
        nullable=True
    )

    conductor = relationship("Conductor")
    pasajero = relationship("Pasajero")
    acompanante = relationship("Acompanante")

