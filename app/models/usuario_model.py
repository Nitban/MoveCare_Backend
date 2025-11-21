from sqlalchemy import Column, String, Boolean, Integer, Text, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from app.core.database import Base
import uuid


class Usuario(Base):
    __tablename__ = "usuario"

    id_usuario = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    uid_firebase = Column(String, unique=True, nullable=False)     # agregar a BD
    nombre_completo = Column(String, nullable=False)
    edad = Column(Integer, nullable=False)
    direccion = Column(Text, nullable=False)
    correo = Column(String, unique=True, nullable=False)
    telefono = Column(String, nullable=False)
    discapacidad = Column(Text)
    foto_ine = Column(Text, nullable=False)                        # nombre correcto
    rol = Column(String, nullable=False)                           # pasajero/conductor
    activo = Column(Boolean, default=False)
    autentificado = Column(Boolean, default=False)                 # email verificado
    fecha_registro = Column(TIMESTAMP, server_default=func.now())

