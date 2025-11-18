from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship
from app.core.database import Base

class Usuario(Base):
    __tablename__ = "usuario"

    id = Column(Integer, primary_key=True, index=True)
    uid_firebase = Column(String, unique=True, nullable=False)

    nombre_completo = Column(String, nullable=False)
    edad = Column(Integer, nullable=False)
    direccion = Column(String, nullable=False)
    telefono = Column(String, nullable=False)
    correo = Column(String, unique=True, nullable=False)

    discapacidad = Column(String, nullable=True)
    tipo_usuario = Column(String, nullable=False)  # "pasajero" o "conductor"

    foto_ine_url = Column(String, nullable=False)
    activo = Column(Boolean, default=False)

    pasajero = relationship("Pasajero", back_populates="usuario", uselist=False)
    conductor = relationship("Conductor", back_populates="usuario", uselist=False)