from app.core.database import Base
from sqlalchemy import Column, Integer, ForeignKey, String
from sqlalchemy.orm import relationship


class Conductor(Base):
    __tablename__ = "conductor"

    id = Column(Integer, primary_key=True)
    id_usuario = Column(Integer, ForeignKey("usuario.id"))

    licencia_url = Column(String, nullable=False)
    usuario = relationship("Usuario", back_populates="conductor")
