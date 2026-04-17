from sqlalchemy import Column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base

class Administrador(Base):
    __tablename__ = "administrador"

    id_administrador = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(UUID(as_uuid=True), ForeignKey("usuario.id_usuario"), nullable=False)

    usuario = relationship("Usuario", back_populates="administrador")
    reporte = relationship("Reporte", back_populates="administrador")