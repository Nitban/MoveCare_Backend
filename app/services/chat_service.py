from sqlalchemy.orm import Session
from app.models.chat_model import MensajeChat
from app.models.viaje_model import Viaje


class ChatService:

    @staticmethod
    def enviar_mensaje(db: Session, id_viaje: str, id_emisor: str, contenido: str):
        # 1. Opcional pero recomendado: Validar que el viaje exista y esté activo
        viaje = db.query(Viaje).filter(Viaje.id_viaje == id_viaje).first()
        if not viaje:
            raise ValueError("El viaje especificado no existe.")

        if viaje.estado in ["Cancelado", "Finalizado"]:
            raise ValueError("No se pueden enviar mensajes en un viaje finalizado o cancelado.")

        # 2. Crear y guardar el mensaje
        nuevo_mensaje = MensajeChat(
            id_viaje=id_viaje,
            id_emisor=id_emisor,
            contenido=contenido
        )

        db.add(nuevo_mensaje)
        db.commit()
        db.refresh(nuevo_mensaje)

        return nuevo_mensaje

    @staticmethod
    def obtener_historial_chat(db: Session, id_viaje: str):
        # Recuperamos todos los mensajes ordenados del más antiguo al más reciente
        return (
            db.query(MensajeChat)
            .filter(MensajeChat.id_viaje == id_viaje)
            .order_by(MensajeChat.fecha_envio.asc())
            .all()
        )