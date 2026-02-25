from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.pagos_model import MetodoPago, CuentaBancaria
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.schemas.pagos import MetodoPagoCreate, CuentaBancariaCreate


class PagosService:

    # --- HELPERS ---
    @staticmethod
    def _get_pasajero(db: Session, id_usuario: str) -> Pasajero:
        p = db.query(Pasajero).filter(Pasajero.id_usuario == id_usuario).first()
        if not p: raise HTTPException(404, "Usuario no es pasajero")
        return p

    @staticmethod
    def _get_conductor(db: Session, id_usuario: str) -> Conductor:
        c = db.query(Conductor).filter(Conductor.id_usuario == id_usuario).first()
        if not c: raise HTTPException(404, "Usuario no es conductor")
        return c

    # ================= PASAJERO: METODOS DE PAGO =================
    @staticmethod
    def crear_metodo_pago(db: Session, id_usuario: str, data: MetodoPagoCreate):
        # ... este se queda igualito ...
        pasajero = PagosService._get_pasajero(db, id_usuario)

        nuevo_metodo = MetodoPago(
            alias=data.alias,
            token_tarjeta=data.token_tarjeta,
            ultimos_cuatro=data.ultimos_cuatro,
            marca=data.marca,
            id_pasajero=pasajero.id_pasajero
        )
        db.add(nuevo_metodo)
        db.commit()
        db.refresh(nuevo_metodo)
        return nuevo_metodo

    @staticmethod
    def listar_metodos_pago(db: Session, id_usuario: str):
        pasajero = PagosService._get_pasajero(db, id_usuario)
        # 🔥 Modificado: Solo trae los que tienen activo == True
        return db.query(MetodoPago).filter(
            MetodoPago.id_pasajero == pasajero.id_pasajero,
            MetodoPago.activo == True
        ).all()

    @staticmethod
    def deshabilitar_metodo_pago(db: Session, id_usuario: str, id_metodo: str):
        pasajero = PagosService._get_pasajero(db, id_usuario)

        # Buscamos la tarjeta asegurándonos de que le pertenezca a ESTE pasajero
        metodo = db.query(MetodoPago).filter(
            MetodoPago.id_metodo == id_metodo,
            MetodoPago.id_pasajero == pasajero.id_pasajero,
            MetodoPago.activo == True
        ).first()

        if not metodo:
            raise HTTPException(status_code=404, detail="Método de pago no encontrado o ya fue eliminado")

        # Hacemos el Soft Delete
        metodo.activo = False
        db.commit()

        return {"mensaje": "Método de pago eliminado correctamente"}

    # ================= CONDUCTOR: CUENTAS BANCARIAS =================
    @staticmethod
    def crear_cuenta_bancaria(db: Session, id_usuario: str, data: CuentaBancariaCreate):
        conductor = PagosService._get_conductor(db, id_usuario)

        nueva_cuenta = CuentaBancaria(
            banco=data.banco,
            token_cuenta=data.token_cuenta,
            titular=data.titular,
            ultimos_cuatro=data.ultimos_cuatro,
            id_conductor=conductor.id_conductor
        )
        db.add(nueva_cuenta)
        db.commit()
        db.refresh(nueva_cuenta)
        return nueva_cuenta

    @staticmethod
    def listar_cuentas_bancarias(db: Session, id_usuario: str):
        conductor = PagosService._get_conductor(db, id_usuario)
        return db.query(CuentaBancaria).filter(CuentaBancaria.id_conductor == conductor.id_conductor).all()