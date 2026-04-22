from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import stripe
from app.models.pagos_model import MetodoPago, CuentaBancaria
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.models.viaje_model import Viaje  # Asegúrate de que esta ruta sea correcta
from app.schemas.pagos import MetodoPagoCreate, CuentaBancariaCreate, CobroTokenRequest


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

    # ================= WEBHOOKS (STRIPE) =================
    @staticmethod
    def marcar_viaje_pagado(db: Session, id_viaje: str):
        viaje = db.query(Viaje).filter(Viaje.id_viaje == id_viaje).first()
        if viaje:
            viaje.estado_pago = "PAGADO"
            db.commit()
            print(f"Viaje {id_viaje} actualizado a PAGADO")

    @staticmethod
    def marcar_viaje_fallido(db: Session, id_viaje: str):
        viaje = db.query(Viaje).filter(Viaje.id_viaje == id_viaje).first()
        if viaje:
            viaje.estado_pago = "FALLIDO"
            db.commit()
            print(f"Viaje {id_viaje} marcado como FALLIDO")

    # ================= PASAJERO: METODOS DE PAGO =================
    @staticmethod
    def crear_metodo_pago(db: Session, id_usuario: str, data: MetodoPagoCreate):
        pasajero = PagosService._get_pasajero(db, id_usuario)

        # 1. Buscar si ya existe un stripe_customer_id en alguna de sus tarjetas
        tarjeta_previa = db.query(MetodoPago).filter(
            MetodoPago.id_pasajero == pasajero.id_pasajero,
            MetodoPago.stripe_customer_id.isnot(None)
        ).first()

        stripe_customer_id = tarjeta_previa.stripe_customer_id if tarjeta_previa else None

        # 2. Si es su primera tarjeta, crear el Customer en Stripe
        if not stripe_customer_id:
            try:
                # Accedemos a la info del usuario a través de la relación en Pasajero
                customer = stripe.Customer.create(
                    name=pasajero.usuario.nombre_completo,
                    email=pasajero.usuario.correo,
                    metadata={"id_pasajero": str(pasajero.id_pasajero)}
                )
                stripe_customer_id = customer.id
            except stripe.error.StripeError as e:
                raise HTTPException(400, detail=f"Error en Stripe Customer: {str(e.user_message)}")

        # 3. Vincular la tarjeta al Customer
        try:
            stripe.PaymentMethod.attach(
                data.token_tarjeta,
                customer=stripe_customer_id,
            )
            # Configurarla como predeterminada (opcional pero recomendado)
            stripe.Customer.modify(
                stripe_customer_id,
                invoice_settings={"default_payment_method": data.token_tarjeta},
            )
        except stripe.error.StripeError as e:
            raise HTTPException(400, detail=f"Error al vincular tarjeta: {str(e.user_message)}")

        # 4. Guardar en BD local
        nuevo_metodo = MetodoPago(
            alias=data.alias,
            token_tarjeta=data.token_tarjeta,
            ultimos_cuatro=data.ultimos_cuatro,
            marca=data.marca,
            stripe_customer_id=stripe_customer_id,
            id_pasajero=pasajero.id_pasajero
        )
        db.add(nuevo_metodo)
        db.commit()
        db.refresh(nuevo_metodo)
        return nuevo_metodo

    @staticmethod
    def cobrar_con_tarjeta_guardada(db: Session, id_usuario: str, data: CobroTokenRequest):
        """
        Realiza un cobro 'Off-Session' (sin que el usuario esté presente).
        """
        pasajero = PagosService._get_pasajero(db, id_usuario)

        # Obtener la tarjeta de nuestra BD
        metodo = db.query(MetodoPago).filter(
            MetodoPago.id_metodo == data.id_metodo,
            MetodoPago.id_pasajero == pasajero.id_pasajero,
            MetodoPago.activo == True
        ).first()

        if not metodo:
            raise HTTPException(404, "Método de pago no encontrado")

        try:
            # Crear y confirmar el pago inmediatamente
            intent = stripe.PaymentIntent.create(
                amount=int(data.monto * 100),
                currency="mxn",
                customer=metodo.stripe_customer_id,
                payment_method=metodo.token_tarjeta,
                off_session=True,  # Indica que el usuario no está en la app
                confirm=True,  # Intenta cobrar de una vez
                metadata={"id_viaje": str(data.id_viaje)}
            )
            return {"status": "success", "payment_intent_id": intent.id}

        except stripe.error.CardError as e:
            # Error de tarjeta (fondos insuficientes, etc)
            err = e.error
            raise HTTPException(400, detail=f"Error de cargo: {err.message}")
        except stripe.error.StripeError as e:
            raise HTTPException(500, detail="Error interno en Stripe")

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
            raise HTTPException(404, detail="Método de pago no encontrado")

        metodo.activo = False
        db.commit()

        # Desvincular de Stripe para mayor seguridad
        try:
            stripe.PaymentMethod.detach(metodo.token_tarjeta)
        except:
            pass  # Si falla en Stripe (ej. ya borrada), igual la desactivamos localmente

        return {"mensaje": "Método de pago eliminado"}

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