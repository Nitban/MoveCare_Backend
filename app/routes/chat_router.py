from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.core.security import get_current_user # Asumiendo que esta es tu dependencia de Auth
from app.schemas.chat import MensajeCreate, MensajeResponse
from app.services.chat_service import ChatService

router = APIRouter(prefix="/chat", tags=["Chat"])

@router.post("/enviar", response_model=MensajeResponse)
def enviar_mensaje(
    data: MensajeCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)  # Funciona tanto para pasajero como conductor
):
    try:
        # El id_emisor lo tomamos del token de seguridad, NO de lo que envíe el cliente (por seguridad)
        mensaje = ChatService.enviar_mensaje(
            db=db,
            id_viaje=str(data.id_viaje),
            id_emisor=str(user["id_usuario"]),
            contenido=data.contenido
        )
        return mensaje
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error del servidor: {str(e)}")

@router.get("/{id_viaje}", response_model=List[MensajeResponse])
def obtener_historial(
    id_viaje: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    try:
        # Aquí podrías añadir lógica para validar que el usuario que consulta
        # sea realmente el conductor o el pasajero de ESE viaje (seguridad E2E)
        mensajes = ChatService.obtener_historial_chat(db, id_viaje)
        return mensajes
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener chat: {str(e)}")