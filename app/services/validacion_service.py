from sqlalchemy.orm import Session
from fastapi import HTTPException
from app.models.validacion_model import ValidacionUsuario
from app.schemas.validacion import ValidacionUsuarioCreate


class ValidacionService:

    @staticmethod
    def crear_validacion(db: Session, id_usuario: str, data: ValidacionUsuarioCreate):
        # 1. Verificamos si ya tiene una validación en proceso para no duplicar
        validacion_existente = db.query(ValidacionUsuario).filter(
            ValidacionUsuario.id_usuario == id_usuario
        ).first()

        if validacion_existente:
            # Si ya existe, podríamos actualizarla en lugar de crear una nueva
            validacion_existente.ine_frente = data.ine_frente
            validacion_existente.ine_reverso = data.ine_reverso
            validacion_existente.estado_validacion = "Pendiente"  # Regresa a pendiente por si había sido rechazada
            db.commit()
            db.refresh(validacion_existente)
            return validacion_existente

        # 2. Si no existe, creamos el registro nuevo
        nueva_validacion = ValidacionUsuario(
            id_usuario=id_usuario,  # 🔥 Aquí inyectamos el ID seguro
            ine_frente=data.ine_frente,
            ine_reverso=data.ine_reverso
        )

        db.add(nueva_validacion)
        db.commit()
        db.refresh(nueva_validacion)
        return nueva_validacion