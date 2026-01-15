from sqlalchemy import Column, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid
from app.core.database import Base


class Conductor(Base):
    __tablename__ = "conductor"

    id_conductor = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    id_usuario = Column(
        UUID(as_uuid=True),
        ForeignKey("usuario.id_usuario", ondelete="CASCADE"),
        nullable=False
    )
    licencia_conduccion = Column(Text, nullable=False)

    usuario = relationship("Usuario", back_populates="conductor")

    # CAMBIO IMPORTANTE AQUÍ:
    #vehiculos = relationship(
        #"Vehiculos",
       # back_populates="conductor",
      #  cascade="all, delete-orphan",
        # Usamos string para decirle explícitamente qué columna en la otra tabla es la llave
     #   foreign_keys="[Vehiculos.id_conductor]"
    #)