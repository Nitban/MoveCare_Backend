from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.models.viaje_model import Viaje
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.models.administrador_model import Administrador
from app.models.usuario_model import Usuario
from datetime import datetime


class AppService:

    @staticmethod
    def get_home_pasajero(db: Session, id_usuario: str):
        now = datetime.now()

        usuario = (
            db.query(Usuario)
            .join(Pasajero)
            .filter(Usuario.id_usuario == id_usuario)
            .first()
        )

        if not usuario:
            return None

        # --- VIAJE PRÓXIMO (Filtrado por tiempo actual) ---
        viaje_proximo = (
            db.query(
                Viaje,
                Usuario.nombre_completo.label("nombre_conductor"),
                Conductor
            )
            .outerjoin(Conductor, Conductor.id_conductor == Viaje.id_conductor)
            .outerjoin(Usuario, Usuario.id_usuario == Conductor.id_usuario)
            .filter(
                Viaje.id_pasajero == usuario.pasajero.id_pasajero,
                Viaje.estado.in_(["Agendado", "En_curso"]),
                Viaje.fecha_hora_inicio >= now  # 🔥 Filtro para no mostrar viajes pasados
            )
            .order_by(Viaje.fecha_hora_inicio.asc())
            .first()
        )

        # --- HISTORIAL (Solo finalizados) ---
        historial = (
            db.query(
                Viaje,
                Usuario.nombre_completo.label("nombre_conductor")
            )
            .outerjoin(Conductor, Conductor.id_conductor == Viaje.id_conductor)
            .outerjoin(Usuario, Usuario.id_usuario == Conductor.id_usuario)
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
                "id_viaje": str(viaje.id_viaje),
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "destino": viaje.destino,
                "estado": viaje.estado,
                "conductor_nombre": nombre_conductor or "No asignado"
            })

        viaje_data = None
        if viaje_proximo:
            viaje, nombre_conductor, conductor = viaje_proximo
            # Obtener vehículo del conductor (usando backref 'vehiculos')
            vehiculo = conductor.vehiculos[0] if (conductor and getattr(conductor, 'vehiculos', None)) else None

            viaje_data = {
                "id_viaje": str(viaje.id_viaje),
                "punto_inicio": getattr(viaje, 'punto_inicio', "Desconocido"),
                "destino": viaje.destino,
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "estado": viaje.estado,
                "nombre_conductor": nombre_conductor or "Asignando...",
                "vehiculo_marca": vehiculo.marca if vehiculo else "N/A",
                "vehiculo_modelo": vehiculo.modelo if vehiculo else "N/A",
                "vehiculo_color": vehiculo.color if vehiculo else "N/A",
                "vehiculo_placas": vehiculo.placas if vehiculo else "N/A",
                "vehiculo_accesorios": vehiculo.accesorios if vehiculo else "Ninguno",
                "ruta": getattr(viaje, 'ruta', None)
            }

        return {
            "usuario": {
                "id_usuario": str(usuario.id_usuario),
                "nombre_completo": usuario.nombre_completo,
                "correo": usuario.correo,
                "telefono": usuario.telefono,
                "direccion": usuario.direccion,
                "fecha_nacimiento": usuario.fecha_nacimiento.isoformat() if usuario.fecha_nacimiento else None,
                "foto_perfil": usuario.foto_perfil,
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
        now = datetime.now()

        usuario = (
            db.query(Usuario)
            .join(Conductor)
            .filter(Usuario.id_usuario == id_usuario)
            .first()
        )

        if not usuario or not getattr(usuario, 'conductor', None):
            return {"usuario": None, "viaje_proximo": None, "historial": []}

        # --- VIAJE PRÓXIMO ---
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
                Viaje.estado.in_(["Agendado", "En_curso"]),
                Viaje.fecha_hora_inicio >= now  # 🔥 Filtro para evitar viajes pasados
            )
            .order_by(Viaje.fecha_hora_inicio.asc())
            .first()
        )

        # --- HISTORIAL ---
        historial_query = (
            db.query(
                Viaje,
                Usuario.telefono.label("telefono_pasajero"),
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

        historial_json = []
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

        viaje_data = None
        if viaje_proximo_query:
            viaje, nombre, necesidad, telefono = viaje_proximo_query

            viaje_data = {
                "id_viaje": str(viaje.id_viaje),
                "punto_inicio": getattr(viaje, 'punto_inicio', "Desconocido"),
                "destino": viaje.destino,
                "fecha_hora_inicio": viaje.fecha_hora_inicio.isoformat(),
                "estado": viaje.estado,
                "nombre_pasajero": nombre or "Desconocido",
                "telefono_pasajero": telefono,
                "necesidad_especial": necesidad,
                "ruta": getattr(viaje, 'ruta', None),
                "lat_inicio": getattr(viaje, 'lat_inicio', None),
                "lng_inicio": getattr(viaje, 'lng_inicio', None),
                "lat_destino": getattr(viaje, 'lat_destino', None),
                "lng_destino": getattr(viaje, 'lng_destino', None),
            }

        return {
            "usuario": {
                "id_usuario": str(usuario.id_usuario),
                "nombre_completo": usuario.nombre_completo,
                "correo": usuario.correo,
                "telefono": usuario.telefono,
                "direccion": usuario.direccion,
                "fecha_nacimiento": usuario.fecha_nacimiento.isoformat() if usuario.fecha_nacimiento else None,
                "foto_perfil": usuario.foto_perfil,
                "rol": usuario.rol,
                "id_conductor": str(usuario.conductor.id_conductor),
                "activo": usuario.activo
            },
            "viaje_proximo": viaje_data,
            "historial": historial_json
        }

    @staticmethod
    def get_home_administrador(db: Session, id_usuario: str):  # Cambiamos el nombre del parámetro por claridad
        # 1. Buscar al administrador por su id_usuario (que es el que viene del token)
        administrador = (
            db.query(Administrador)
            .filter(Administrador.id_usuario == id_usuario)  # <-- EL CAMBIO CLAVE ESTÁ AQUÍ
            .first()
        )

        if not administrador:
            return {"usuario": None, "error": "Administrador no encontrado"}

        # 2. Ahora buscamos la información del Usuario
        usuario = (
            db.query(Usuario)
            .filter(Usuario.id_usuario == id_usuario)  # Podemos usar directamente el id_usuario
            .first()
        )

        if not usuario:
            return {"usuario": None, "error": "Usuario asociado no encontrado"}

        # 3. Retornar la información formateada
        return {
            "usuario": {
                "id_usuario": str(usuario.id_usuario),
                "nombre_completo": usuario.nombre_completo,  # 1. Cambiamos la llave a "nombre"
                "correo": usuario.correo,
                "telefono": usuario.telefono,
                "direccion": usuario.direccion,
                "fecha_nacimiento": usuario.fecha_nacimiento.isoformat() if usuario.fecha_nacimiento else None,
                "foto_perfil": usuario.foto_perfil if usuario.foto_perfil and usuario.foto_perfil != "N/A" else "",
                "rol": usuario.rol,
                "id_administrador": str(administrador.id_administrador),
                "activo": usuario.activo
            }
        }