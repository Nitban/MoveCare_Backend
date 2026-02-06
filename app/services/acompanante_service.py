from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.acompanante_model import Acompanante
from app.models.pasajero_model import Pasajero
from app.schemas.acompanante import AcompananteCreate

class AcompananteService:

    @staticmethod
    def _get_pasajero_by_usuario(db: Session, id_usuario: str) -> Pasajero:
        pasajero = db.query(Pasajero).filter(Pasajero.id_usuario == id_usuario).first()
        if not pasajero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no es pasajero"
            )
        return pasajero

    @staticmethod
    def crear(db: Session, id_usuario: str, data: AcompananteCreate):
        pasajero = AcompananteService._get_pasajero_by_usuario(db, id_usuario)

        acompanante = Acompanante(
            nombre_completo=data.nombre_completo,
            parentesco=data.parentesco,
            ine_frente=data.ine_frente,
            ine_reverso=data.ine_reverso,
            id_pasajero=pasajero.id_pasajero
        )

        db.add(acompanante)
        db.commit()
        db.refresh(acompanante)
        return acompanante

    @staticmethod
    def listar_por_usuario(db: Session, id_usuario: str):
        pasajero = AcompananteService._get_pasajero_by_usuario(db, id_usuario)
        return db.query(Acompanante).filter(
            Acompanante.id_pasajero == pasajero.id_pasajero
        ).order_by(Acompanante.nombre_completo.asc()).all()