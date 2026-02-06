from sqlalchemy import Column, String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Acompanante(Base):
    __tablename__ = "acompanante"

    id_acompanante = Column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4
    )
    nombre_completo = Column(String, nullable=False)
    parentesco = Column(String, nullable=True)
    ine_frente = Column(Text, nullable=True)
    ine_reverso = Column(Text, nullable=True)

    id_pasajero = Column(
        UUID(as_uuid=True),
        ForeignKey("pasajero.id_pasajero", ondelete="CASCADE"),
        nullable=False
    )

    pasajero = relationship("Pasajero", back_populates="acompanantes")