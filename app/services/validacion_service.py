from sqlalchemy.orm import Session

from app.models.usuario_model import Usuario
from app.models.validacion_model import ValidacionUsuario
from app.schemas.validacion import ValidacionUsuarioCreate

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
    def aceptar_validacion(db: Session, id_validacion: str):
        validacion = db.query(ValidacionUsuario).filter(
            ValidacionUsuario.id_validacion == id_validacion
        ).first()

        if not validacion:
            raise Exception("Validación no encontrada")

        validacion.estado_validacion = "Aceptado"
        db.commit()
        db.refresh(validacion)
        return validacion

    @staticmethod
    def rechazar_validacion(db: Session, id_validacion: str, motivo: str):
        validacion = db.query(ValidacionUsuario).filter(
            ValidacionUsuario.id_validacion == id_validacion
        ).first()

        if not validacion:
            raise Exception("Validación no encontrada")

        validacion.estado_validacion = "Rechazado"
        validacion.motivo_rechazo = motivo
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
                    "nombre": usuario.nombre_completo,  # Cambia esto si tu campo se llama distinto (ej. nombres)
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