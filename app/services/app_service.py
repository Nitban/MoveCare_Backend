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
                "telefono": usuario.telefono,
                "direccion": usuario.direccion,
                "fecha_nacimiento": usuario.fecha_nacimiento,
                "foto_perfil":usuario.foto_perfil,
                "discapacidad": usuario.discapacidad,
                "rol": usuario.rol,
                "id_pasajero": str(usuario.pasajero.id_pasajero),
                "activo": usuario.activo
            },
            "viaje_proximo": viaje_data,
            "historial": historial_json
        }

    @staticmethod
    def get_home_conductor(db: Session, id_usuario: str):
        # 1. Obtenemos el usuario conductor
        usuario = (
            db.query(Usuario)
            .join(Conductor)
            .filter(Usuario.id_usuario == id_usuario)
            .first()
        )

        if not usuario or not getattr(usuario, 'conductor', None):
            return {"usuario": None, "viaje_proximo": None, "historial": []}

        # 2. Obtenemos el viaje próximo (Aquí pides 4 cosas)
        viaje_proximo_query = (
            db.query(
                Viaje,
                Usuario.nombre_completo.label("nombre_pasajero"),
                Usuario.discapacidad.label("necesidad_especial"),
                Usuario.telefono.label("telefono_pasajero")
            )
            .join(Pasajero, Pasajero.id_pasajero == Viaje.id_pasajero)
            .join(Usuario, Usuario.id_usuario == Pasajero.id_usuario)
            .filter(
                Viaje.id_conductor == usuario.conductor.id_conductor,
                Viaje.estado.in_(["Agendado", "En_curso"])
            )
            .order_by(Viaje.fecha_hora_inicio.asc())
            .first()
        )

        # 3. Obtenemos el historial (Faltaba el teléfono en la query)
        historial_query = (
            db.query(
                Viaje,
                Usuario.telefono.label("telefono_pasajero"),  # <--- Agregado
                Usuario.nombre_completo.label("nombre_pasajero"),
                Usuario.discapacidad.label("necesidad_especial")
            )
            .join(Pasajero, Pasajero.id_pasajero == Viaje.id_pasajero)
            .join(Usuario, Usuario.id_usuario == Pasajero.id_usuario)
            .filter(
                Viaje.id_conductor == usuario.conductor.id_conductor,
                Viaje.estado == "Finalizado"
            )
            .order_by(Viaje.fecha_hora_inicio.desc())
            .all()
        )

        # 4. Formateamos el historial a JSON
        historial_json = []
        # Ahora sí coinciden las 4 variables con las 4 columnas de la query
        for viaje, telefono, nombre, necesidad in historial_query:
            historial_json.append({
                "id_viaje": str(viaje.id_viaje),
                "punto_inicio": getattr(viaje, 'punto_inicio', "Desconocido"),
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "destino": viaje.destino,
                "estado": viaje.estado,
                "nombre_pasajero": nombre or "Desconocido",
                "telefono_pasajero": telefono,
                "necesidad_especial": necesidad
            })

        # 5. Formateamos el viaje próximo a JSON
        viaje_data = None
        if viaje_proximo_query:
            # Aquí también corregimos el desempaquetado (antes esperabas 3, pero llegan 4)
            viaje, nombre, necesidad, telefono = viaje_proximo_query

            viaje_data = {
                "id_viaje": str(viaje.id_viaje),
                "punto_inicio": getattr(viaje, 'punto_inicio', "Desconocido"),
                "destino": viaje.destino,
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "estado": viaje.estado,
                "nombre_pasajero": nombre or "Desconocido",
                "telefono_pasajero": telefono,  # <--- Agregado para que Flutter pueda llamar
                "necesidad_especial": necesidad,
                "ruta": getattr(viaje, 'ruta', None),
                # Agregamos coordenadas si existen en tu modelo para el widget del mapa
                "lat_inicio": getattr(viaje, 'lat_inicio', None),
                "lng_inicio": getattr(viaje, 'lng_inicio', None),
                "lat_destino": getattr(viaje, 'lat_destino', None),
                "lng_destino": getattr(viaje, 'lng_destino', None),
            }

        # 6. Estructuramos la respuesta final
        return {
            "usuario": {
                "id_usuario": str(usuario.id_usuario),
                "nombre_completo": usuario.nombre_completo,
                "correo": usuario.correo,
                "telefono": usuario.telefono,
                "direccion": usuario.direccion,
                "fecha_nacimiento": usuario.fecha_nacimiento,
                "foto_perfil": usuario.foto_perfil,
                "rol": usuario.rol,
                "id_conductor": str(usuario.conductor.id_conductor),
                "activo": usuario.activo
            },
            "viaje_proximo": viaje_data,
            "historial": historial_json
        }