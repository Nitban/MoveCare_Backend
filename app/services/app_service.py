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

        # 🔥 CAMBIO 1: Agregamos el modelo Conductor a la consulta
        # para poder acceder a sus vehículos a través del backref
        viaje_proximo = (
            db.query(
                Viaje,
                Usuario.nombre_completo.label("nombre_conductor"),
                Conductor
            )
            .outerjoin(
                Conductor, Conductor.id_conductor == Viaje.id_conductor
            )
            .outerjoin(
                Usuario, Usuario.id_usuario == Conductor.id_usuario
            )
            .filter(
                Viaje.id_pasajero == usuario.pasajero.id_pasajero,
                Viaje.estado.in_(["Agendado", "En_curso"])  # Al cancelar el viaje, ya no aparecerá aquí
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
                "id_viaje": str(viaje.id_viaje),  # Convertido a str por seguridad con UUID
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "destino": viaje.destino,
                "estado": viaje.estado,
                "conductor_nombre": nombre_conductor or ""
            })  # Faltaba cerrar el paréntesis de este diccionario en tu código original

        viaje_data = None

        if viaje_proximo:
            # 🔥 CAMBIO 2: Desempaquetamos los 3 elementos de la consulta
            viaje, nombre_conductor, conductor = viaje_proximo

            # 🔥 CAMBIO 3: Obtenemos el vehículo (conductor.vehiculos es una lista gracias al backref)
            vehiculo = conductor.vehiculos[0] if (conductor and getattr(conductor, 'vehiculos', None)) else None

            # 🔥 CAMBIO 4: Llenamos el diccionario con toda la info para el modal del frontend
            viaje_data = {
                "id_viaje": str(viaje.id_viaje),
                "punto_inicio": getattr(viaje, 'punto_inicio', "Desconocido"),  # Extraemos el origen
                "destino": viaje.destino,
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "estado": viaje.estado,
                "nombre_conductor": nombre_conductor or "Asignando...",
                "vehiculo_marca": vehiculo.marca if vehiculo else "N/A",
                "vehiculo_modelo": vehiculo.modelo if vehiculo else "N/A",
                "vehiculo_color": vehiculo.color if vehiculo else "N/A",
                "vehiculo_placas": vehiculo.placas if vehiculo else "N/A",
                "vehiculo_accesorios": vehiculo.accesorios if vehiculo else "Ninguno",
                "ruta": getattr(viaje, 'ruta', None)  # Extraemos la ruta para dibujar el mapa
            }

        return {
            "usuario": {
                "id_usuario": str(usuario.id_usuario),
                "nombre_completo": usuario.nombre_completo,
                "correo": usuario.correo,
                "rol": usuario.rol,
                "id_pasajero": str(usuario.pasajero.id_pasajero),
                "activo": usuario.activo
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