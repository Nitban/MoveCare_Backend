from app.core.database import Base
from app.models.usuario_model import Usuario
from app.models.conductor_model import Conductor
from app.models.pasajero_model import Pasajero
from app.models.vehiculo_model import Vehiculos

# Esto permite que Base.metadata tenga registro de todas las tablas
__all__ = ["Base", "Usuario", "Conductor", "Pasajero", "Vehiculos"]