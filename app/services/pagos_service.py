from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import stripe  # 🔥 Importante si llegas a interactuar con la API de Stripe desde aquí

from app.models.pagos_model import MetodoPago, CuentaBancaria
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
# from app.models.viaje_model import Viaje  <-- Importa tu modelo de Viaje aquí
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

    # ================= NUEVO: WEBHOOKS (STRIPE) =================
    @staticmethod
    def marcar_viaje_pagado(db: Session, id_viaje: str):
        """
        Esta función es llamada EXCLUSIVAMENTE por el Webhook de Stripe
        cuando el cobro a la tarjeta fue exitoso.
        """
        # Ejemplo de cómo deberías actualizar tu base de datos:
        # viaje = db.query(Viaje).filter(Viaje.id_viaje == id_viaje).first()
        # if no viaje:
        #     raise HTTPException(404, "Viaje no encontrado para actualizar pago")
        #
        # viaje.estado_pago = "PAGADO"
        # db.commit()
        # db.refresh(viaje)
        # return viaje
        print(f"Lógica del servicio: Actualizando viaje {id_viaje} a PAGADO")
        pass

    @staticmethod
    def marcar_viaje_fallido(db: Session, id_viaje: str):
        """
        Llamado por el Webhook si la tarjeta fue declinada o no tiene fondos.
        """
        # viaje = db.query(Viaje).filter(Viaje.id_viaje == id_viaje).first()
        # viaje.estado_pago = "FALLIDO"
        # db.commit()
        print(f"Lógica del servicio: El pago del viaje {id_viaje} FALLÓ")
        pass

    # ================= PASAJERO: METODOS DE PAGO =================
    @staticmethod
    def crear_metodo_pago(db: Session, id_usuario: str, data: MetodoPagoCreate):
        """
        OJO CON STRIPE:
        El campo 'token_tarjeta' de tu esquema ahora debe guardar el ID del
        'PaymentMethod' de Stripe (que empieza con 'pm_...', ej: pm_1N5O...).
        ¡Nunca guardes los 16 dígitos de la tarjeta reales!
        """
        pasajero = PagosService._get_pasajero(db, id_usuario)

        nuevo_metodo = MetodoPago(
            alias=data.alias,
            token_tarjeta=data.token_tarjeta,  # Aquí va el ID de Stripe: "pm_xxxxxxxx"
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
        return db.query(MetodoPago).filter(
            MetodoPago.id_pasajero == pasajero.id_pasajero,
            MetodoPago.activo == True
        ).all()

    @staticmethod
    def deshabilitar_metodo_pago(db: Session, id_usuario: str, id_metodo: str):
        pasajero = PagosService._get_pasajero(db, id_usuario)

        metodo = db.query(MetodoPago).filter(
            MetodoPago.id_metodo == id_metodo,
            MetodoPago.id_pasajero == pasajero.id_pasajero,
            MetodoPago.activo == True
        ).first()

        if not metodo:
            raise HTTPException(status_code=404, detail="Método de pago no encontrado o ya fue eliminado")

        # Soft Delete
        metodo.activo = False
        db.commit()

        # Opcional pero recomendado: Avisarle a Stripe que "desvincule" ese método de pago
        # si también lo tenías guardado en su plataforma.
        # stripe.PaymentMethod.detach(metodo.token_tarjeta)

        return {"mensaje": "Método de pago eliminado correctamente"}

    # ================= CONDUCTOR: CUENTAS BANCARIAS =================
    # Para pagarle a los conductores, usarás Stripe Connect en el futuro.
    # Por ahora, guardar estos datos en tu BD es correcto para tener la referencia.

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