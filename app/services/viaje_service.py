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

        es_multi_destino = getattr(data, "check_destinos", False)

        destinos_procesados = None
        if es_multi_destino and data.destinos:
            # Usamos model_dump() para Pydantic V2 o dict() para V1
            destinos_procesados = [
                d.model_dump() if hasattr(d, 'model_dump') else d.dict()
                for d in data.destinos
            ]

        viaje = Viaje(
            id_pasajero=pasajero.id_pasajero,
            punto_inicio=data.punto_inicio,

            destino=None if es_multi_destino else data.destino,
            destinos=destinos_procesados if es_multi_destino else None,
            check_destinos=es_multi_destino,

            fecha_hora_inicio=data.fecha_hora_inicio,
            metodo_pago=data.metodo_pago,
            costo=data.costo,
            ruta=None,
            duracion_estimada=data.duracion_estimada,
            fecha_hora_fin=None,
            duracion_real=None,
            cal_pasajero=data.cal_pasajero,
            cal_conductor=data.cal_conductor,
            id_conductor=None,
            especificaciones=data.especificaciones,
            check_acompanante=data.check_acompanante,
            id_acompanante=data.id_acompanante
        )

        db.add(viaje)
        db.commit()
        db.refresh(viaje)

        return viaje