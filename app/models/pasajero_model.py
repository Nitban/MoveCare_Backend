from sqlalchemy import Column, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base
from sqlalchemy.orm import relationship
import uuid

class Pasajero(Base):
    __tablename__ = "pasajero"

    id_pasajero = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False)

    usuario = relationship("Usuario", back_populates="pasajero")

