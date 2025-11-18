from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.core.database import Base

class Pasajero(Base):
    __tablename__ = "pasajero"

    id = Column(Integer, primary_key=True, index=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"))

    usuario = relationship("Usuario", back_populates="pasajero")
