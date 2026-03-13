from sqlalchemy.orm import Session
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