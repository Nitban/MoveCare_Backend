from sqlalchemy import Column, String, ForeignKey, Boolean
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class MetodoPago(Base):
    __tablename__ = "metodo_pago"

    id_metodo = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alias = Column(String, nullable=True)
    token_tarjeta = Column(String, nullable=False)
    ultimos_cuatro = Column(String(4), nullable=False)
    marca = Column(String, nullable=True)
    activo = Column(Boolean, default=True)

    id_pasajero = Column(UUID(as_uuid=True), ForeignKey("pasajero.id_pasajero", ondelete="CASCADE"), nullable=False)

    # Asegúrate de agregar la relación 'metodos_pago' en tu modelo Pasajero
    pasajero = relationship("Pasajero", back_populates="metodos_pago")


class CuentaBancaria(Base):
    __tablename__ = "cuenta_bancaria"

    id_cuenta = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    banco = Column(String, nullable=False)
    token_cuenta = Column(String, nullable=False)
    titular = Column(String, nullable=False)
    ultimos_cuatro = Column(String(4), nullable=False)

    id_conductor = Column(UUID(as_uuid=True), ForeignKey("conductor.id_conductor", ondelete="CASCADE"), nullable=False)

    # Asegúrate de agregar la relación 'cuentas_bancarias' en tu modelo Conductor
    conductor = relationship("Conductor", back_populates="cuentas_bancarias")