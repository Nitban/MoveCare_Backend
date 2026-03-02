from sqlalchemy.orm import Session
from app.models.viaje_model import Viaje
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.models.usuario_model import Usuario
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
            ruta=data.ruta,
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

    @staticmethod
    def obtener_historial_pasajero(db: Session, id_usuario: str):
        # 1. Obtener el id_pasajero vinculado al id_usuario
        pasajero = db.query(Pasajero).filter(Pasajero.id_usuario == id_usuario).first()
        if not pasajero:
            raise ValueError("Pasajero no encontrado")

        # 2. Consultar viajes con Join hacia Conductor y Usuario
        viajes = (
            db.query(Viaje)
            .filter(Viaje.id_pasajero == pasajero.id_pasajero)
            .outerjoin(Conductor, Viaje.id_conductor == Conductor.id_conductor)
            .outerjoin(Usuario, Conductor.id_usuario == Usuario.id_usuario)
            .all()
        )

        resultado = []
        for v in viajes:
            # Formatear fecha a DD/MM/YYYY
            fecha_formateada = v.fecha_hora_inicio.strftime("%d/%m/%Y") if v.fecha_hora_inicio else None

            # Extraer info del conductor si ya fue asignado
            nombre_cond = "Buscando conductor..."
            foto_cond = None

            # Si el viaje ya tiene conductor asignado y el join trajo al usuario
            if v.id_conductor and v.conductor and v.conductor.usuario:
                nombre_cond = v.conductor.usuario.nombre_completo
                foto_cond = getattr(v.conductor.usuario, 'foto_perfil', None)

            resultado.append({
                "id_viaje": v.id_viaje,
                "fecha_inicio": fecha_formateada,
                "punto_inicio": v.punto_inicio,
                "destino": v.destino or "Múltiples destinos",
                "estado": v.estado,  # Asegúrate que tu modelo Viaje tenga este campo
                "nombre_conductor": nombre_cond,
                "foto_conductor": foto_cond
            })

        return resultado

    @staticmethod
    def obtener_historial_conductor(db: Session, id_usuario: str):
        # 1. Obtener el id_conductor vinculado al id_usuario logueado
        conductor = db.query(Conductor).filter(Conductor.id_usuario == id_usuario).first()
        if not conductor:
            raise ValueError("Conductor no encontrado")

        # 2. Consultar viajes: Viaje -> Pasajero -> Usuario (para nombre y discapacidad)
        viajes = (
            db.query(Viaje)
            .filter(Viaje.id_conductor == conductor.id_conductor)
            .join(Pasajero, Viaje.id_pasajero == Pasajero.id_pasajero)
            .join(Usuario, Pasajero.id_usuario == Usuario.id_usuario)
            .order_by(Viaje.fecha_hora_inicio.desc())
            .all()
        )

        resultado = []
        for v in viajes:
            # El join con Usuario a través de Pasajero nos da la info del cliente
            usuario_pasajero = v.pasajero.usuario

            fecha_formateada = v.fecha_hora_inicio.strftime("%d/%m/%Y %H:%M") if v.fecha_hora_inicio else None

            resultado.append({
                "id_viaje": str(v.id_viaje),
                "fecha_inicio": fecha_formateada,
                "punto_inicio": v.punto_inicio,
                "destino": v.destino or "Múltiples destinos",
                "estado": v.estado,
                "costo": v.costo,
                "nombre_pasajero": usuario_pasajero.nombre_completo,
                "foto_pasajero": getattr(usuario_pasajero, 'foto_perfil', None),
                "necesidad_especial": getattr(usuario_pasajero, 'discapacidad', "Ninguna")
            })

        return resultado

    @staticmethod
    def cancelar_viaje(db: Session, id_viaje: str, id_usuario: str):
        # 1. Obtener el pasajero para validar propiedad
        pasajero = db.query(Pasajero).filter(Pasajero.id_usuario == id_usuario).first()
        if not pasajero:
            raise ValueError("Pasajero no encontrado")

        # 2. Buscar el viaje asegurándonos que sea de este pasajero
        viaje = db.query(Viaje).filter(
            Viaje.id_viaje == id_viaje,
            Viaje.id_pasajero == pasajero.id_pasajero
        ).first()

        if not viaje:
            raise ValueError("Viaje no encontrado o no tienes permiso para cancelarlo")

        # 3. Validar que no esté ya cancelado o finalizado
        if viaje.estado in ["Cancelado", "Finalizado"]:
            raise ValueError(f"El viaje no se puede cancelar porque ya está {viaje.estado.lower()}")

        # 4. Cambiar el estado y guardar
        viaje.estado = "Cancelado"
        db.commit()
        db.refresh(viaje)

        return viaje