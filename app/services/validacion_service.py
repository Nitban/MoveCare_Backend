from sqlalchemy.orm import Session
from sqlalchemy import text  # <-- Importante para ejecutar el comando SET LOCAL

from app.models.usuario_model import Usuario
from app.models.administrador_model import Administrador
from app.models.validacion_model import ValidacionUsuario
from app.schemas.validacion import ValidacionUsuarioCreate
from app.models.notificaciones_model import Notificacion

class ValidacionService:

    @staticmethod
    def crear_validacion(db: Session, id_usuario: str, data: ValidacionUsuarioCreate):
        validacion_existente = db.query(ValidacionUsuario).filter(
            ValidacionUsuario.id_usuario == id_usuario
        ).first()

        if validacion_existente:
            validacion_existente.ine_frente = data.ine_frente
            validacion_existente.ine_reverso = data.ine_reverso
            validacion_existente.licencia_frente = data.licencia_frente
            validacion_existente.licencia_reverso = data.licencia_reverso
            validacion_existente.poliza = data.poliza
            validacion_existente.estado_validacion = "Pendiente"
            db.commit()
            db.refresh(validacion_existente)
            return validacion_existente

        nueva_validacion = ValidacionUsuario(
            id_usuario=id_usuario,
            ine_frente=data.ine_frente,
            ine_reverso=data.ine_reverso,
            licencia_frente=data.licencia_frente,
            licencia_reverso=data.licencia_reverso,
            poliza=data.poliza
        )

        db.add(nueva_validacion)
        db.commit()
        db.refresh(nueva_validacion)
        return nueva_validacion

    @staticmethod
    def aceptar_validacion(db: Session, id_validacion: str, id_usuario_admin: str):
        # 1. Buscamos el ID real del administrador usando el id_usuario del token
        admin = db.query(Administrador).filter(Administrador.id_usuario == id_usuario_admin).first()
        if not admin:
            raise Exception("El usuario actual no está registrado como administrador")

        id_admin_real = str(admin.id_administrador)  # <-- Actualizado a id_administrador

        # 2. Buscamos la validación
        validacion = db.query(ValidacionUsuario).filter(
            ValidacionUsuario.id_validacion == id_validacion
        ).first()

        if not validacion:
            raise Exception("Validación no encontrada")

        validacion.estado_validacion = "Aceptado"

        # 3. Creamos la notificación (¡Sin los tres puntitos tramposos!)
        nueva_notificacion = Notificacion(
            id_usuario=validacion.id_usuario,
            titulo="Identificaciones validadas",
            mensaje="Hemos validado tus documentos de forma exitosa. ¡Ya puedes comenzar a usar la plataforma!",
            tipo="validacion_aceptada"
        )
        db.add(nueva_notificacion)

        # 4. Le pasamos el ID REAL a Postgres para la Auditoría
        db.execute(
            text("SET LOCAL app.current_admin = :admin_id"),
            {"admin_id": id_admin_real}
        )

        db.commit()
        db.refresh(validacion)
        return validacion

    @staticmethod
    def rechazar_validacion(db: Session, id_validacion: str, motivo: str, id_usuario_admin: str):
        # 1. Buscamos el ID real del administrador usando el id_usuario del token
        admin = db.query(Administrador).filter(Administrador.id_usuario == id_usuario_admin).first()
        if not admin:
            raise Exception("El usuario actual no está registrado como administrador")

        id_admin_real = str(admin.id_administrador)  # <-- Actualizado a id_administrador

        # 2. Buscamos la validación
        validacion = db.query(ValidacionUsuario).filter(
            ValidacionUsuario.id_validacion == id_validacion
        ).first()

        if not validacion:
            raise Exception("Validación no encontrada")

        # 3. Actualizamos la validación
        validacion.estado_validacion = "Rechazado"
        validacion.motivo_rechazo = motivo

        # 4. Creamos la notificación (¡Con los datos completos!)
        nueva_notificacion = Notificacion(
            id_usuario=validacion.id_usuario,
            titulo="Identificaciones rechazadas",
            mensaje=motivo,
            tipo="validacion_rechazada"
        )
        db.add(nueva_notificacion)

        # 5. Le pasamos el ID REAL a Postgres para la Auditoría
        db.execute(
            text("SET LOCAL app.current_admin = :admin_id"),
            {"admin_id": id_admin_real}
        )

        db.commit()
        db.refresh(validacion)
        return validacion

    @staticmethod
    def obtener_validaciones_pendientes(db: Session):
        # Hacemos un JOIN entre Validación y Usuario, filtrando por estado 'Pendiente'
        resultados = db.query(ValidacionUsuario, Usuario).join(
            Usuario, ValidacionUsuario.id_usuario == Usuario.id_usuario
        ).filter(
            ValidacionUsuario.estado_validacion == "Pendiente"
        ).all()

        pasajeros = []
        conductores = []

        for validacion, usuario in resultados:
            # Construimos el diccionario con la estructura de nuestros schemas
            item = {
                "validacion": validacion,
                "usuario": {
                    "id_usuario": usuario.id_usuario,
                    "nombre": usuario.nombre_completo,  # Cambia esto si tu campo se llama distinto
                    "rol": usuario.rol  # Cambia esto si tu campo de rol se llama distinto
                }
            }

            # Separamos según el rol
            if usuario.rol.lower() == "conductor":
                conductores.append(item)
            else:
                pasajeros.append(item)

        return {
            "pasajeros": pasajeros,
            "conductores": conductores
        }