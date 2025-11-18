from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegistroPasajero, RegistroConductor, LoginSchema
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/registro/pasajero")
def registrar_pasajero(data: RegistroPasajero, db: Session = Depends(get_db)):
    usuario = UsuarioService.crear_usuario(db, data, is_conductor=False)
    return {"mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta."}

@router.post("/registro/conductor")
def registrar_conductor(data: RegistroConductor, db: Session = Depends(get_db)):
    usuario = UsuarioService.crear_usuario(db, data, is_conductor=True)
    return {"mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta."}

@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    token, mensaje = UsuarioService.login(db, data.correo, data.password)
    if token is None:
        raise HTTPException(status_code=401, detail=mensaje)
    return {
        "mensaje": mensaje,
        "token": token
    }
