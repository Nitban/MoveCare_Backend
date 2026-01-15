from sqlalchemy.orm import Session
from app.models.vehiculo_model import Vehiculos

class VehiculoService:

    @staticmethod
    def crear_vehiculo(db: Session, data):
        vehiculo = Vehiculos(
            marca=data.marca,
            modelo=data.modelo,
            placas=data.placas,
            color=data.color,
            capacidad=data.capacidad,
            accesorios=data.accesorios,
            id_conductor=data.id_conductor
        )

        db.add(vehiculo)
        db.commit()
        db.refresh(vehiculo)

        return vehiculo
