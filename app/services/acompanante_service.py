from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.acompanante import Acompanante
from app.models.pasajero import Pasajero
from app.schemas.acompanante_schema import AcompananteCreate


class AcompananteService:

    @staticmethod
    def _get_pasajero_by_usuario(db: Session, id_usuario: str) -> Pasajero:
        pasajero = (
            db.query(Pasajero)
            .filter(Pasajero.id_usuario == id_usuario)
            .first()
        )

        if not pasajero:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="El usuario no es pasajero"
            )

        return pasajero

    # ================= CREAR =================
    @staticmethod
    def crear(db: Session, id_usuario: str, data: AcompananteCreate):
        pasajero = AcompananteService._get_pasajero_by_usuario(
            db, id_usuario
        )

        acompanante = Acompanante(
            nombre_completo=data.nombre_completo,
            foto=data.foto,
            telefono=data.telefono,
            parentesco=data.parentesco,
            id_pasajero=pasajero.id_pasajero
        )

        db.add(acompanante)
        db.commit()
        db.refresh(acompanante)

        return acompanante

    # ================= LISTAR PARA SELECT =================
    @staticmethod
    def listar_por_usuario(db: Session, id_usuario: str):
        pasajero = AcompananteService._get_pasajero_by_usuario(
            db, id_usuario
        )

        acompanantes = (
            db.query(Acompanante)
            .filter(Acompanante.id_pasajero == pasajero.id_pasajero)
            .order_by(Acompanante.nombre_completo.asc())
            .all()
        )

        return acompanantes
