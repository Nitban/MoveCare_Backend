from sqlalchemy.orm import Session
from app.models.viaje_model import Viaje
from app.models.pasajero_model import Pasajero
from datetime import datetime


class ViajeService:

    @staticmethod
    def crear_viaje(db: Session, id_usuario: str, data):

        pasajero = (
            db.query(Pasajero)
            .filter(Pasajero.id_usuario == id_usuario)
            .first()
        )

        if not pasajero:
            raise ValueError("El usuario no es pasajero")

        viaje = Viaje(
            id_pasajero=pasajero.id_pasajero,
            punto_inicio=data.punto_inicio,
            destino=data.destino,
            fecha_hora_inicio=data.fecha_hora_inicio,
            metodo_pago=data.metodo_pago,
            costo=data.costo,
            ruta=data.ruta,
            duracion_estimada=data.duracion_estimada,
            estado="pendiente",
            fecha_hora_fin=None,
            duracion_real=None,
            id_conductor=None
        )

        db.add(viaje)
        db.commit()
        db.refresh(viaje)

        return viaje
