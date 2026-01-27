from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.viaje_model import Viaje
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.models.usuario_model import Usuario
from datetime import datetime


class AppService:

    @staticmethod
    def get_home_pasajero(db: Session, id_usuario: str):
        usuario = (
            db.query(Usuario)
            .join(Pasajero)
            .filter(Usuario.id_usuario == id_usuario)
            .first()
        )

        if not usuario:
            return None

        viaje_proximo = (
            db.query(
                Viaje,
                Usuario.nombre_completo.label("nombre_conductor")
            )
            .outerjoin(
                Conductor, Conductor.id_conductor == Viaje.id_conductor
            )
            .outerjoin(
                Usuario, Usuario.id_usuario == Conductor.id_usuario
            )
            .filter(
                Viaje.id_pasajero == usuario.pasajero.id_pasajero,
                Viaje.estado.in_(["Agendado", "En_curso"])
            )
            .order_by(Viaje.fecha_hora_inicio.asc())
            .first()
        )

        historial = (
            db.query(
                Viaje,
                Usuario.nombre_completo.label("nombre_conductor")
            )
            .outerjoin(
                Conductor,
                Conductor.id_conductor == Viaje.id_conductor
            )
            .outerjoin(
                Usuario,
                Usuario.id_usuario == Conductor.id_usuario
            )
            .filter(
                Viaje.id_pasajero == usuario.pasajero.id_pasajero,
                Viaje.estado == "Finalizado"
            )
            .order_by(Viaje.fecha_hora_inicio.desc())
            .all()
        )

        historial_json = []

        for viaje, nombre_conductor in historial:
            historial_json.append({
                "id_viaje": viaje.id_viaje,
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "destino": viaje.destino,
                "estado": viaje.estado,
                "conductor_nombre": nombre_conductor or ""
            }
        )

        viaje_data = None

        if viaje_proximo:
            viaje, nombre_conductor = viaje_proximo
            viaje_data = {
                "id_viaje": viaje.id_viaje,
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "destino": viaje.destino,
                "estado": viaje.estado,
                "nombre_conductor": nombre_conductor,
            }

        return {
            "usuario": {
                "id_usuario": usuario.id_usuario,
                "nombre_completo": usuario.nombre_completo,
                "correo": usuario.correo,
                "rol": usuario.rol,
                "id_pasajero": usuario.pasajero.id_pasajero
            },
            "viaje_proximo": viaje_data,
            "historial": historial_json
        }

    @staticmethod
    def get_home_conductor(db: Session, id_usuario: str):
        conductor = db.query(Conductor).filter(
            Conductor.id_usuario == id_usuario
        ).first()

        if not conductor:
            return {"viaje_proximo": None, "historial": []}

        ahora = datetime.utcnow()

        viaje_proximo = db.query(Viaje).filter(
            Viaje.id_conductor == conductor.id_conductor,
            Viaje.fecha_hora_inicio >= ahora
        ).order_by(Viaje.fecha_hora_inicio.asc()).first()

        historial = db.query(Viaje).filter(
            Viaje.id_conductor == conductor.id_conductor,
            Viaje.fecha_hora_inicio < ahora
        ).order_by(Viaje.fecha_hora_inicio.desc()).all()

        return {
            "viaje_proximo": viaje_proximo,
            "historial": historial
        }