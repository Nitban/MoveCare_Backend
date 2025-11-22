from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegistroPasajero, RegistroConductor, LoginSchema
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/registro/pasajero")
async def registrar_pasajero(data: RegistroPasajero, db: Session = Depends(get_db)):
    try:
        await UsuarioService.crear_usuario(db, data, is_conductor=False)
        return {"mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/registro/conductor")
async def registrar_conductor(data: RegistroConductor, db: Session = Depends(get_db)):
    try:
        await UsuarioService.crear_usuario(db, data, is_conductor=True)
        return {"mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    token, msg = UsuarioService.login(db, data.correo, data.password)
    if token is None:
        raise HTTPException(status_code=401, detail=msg)
    return {"mensaje": msg, "token": token}

@router.get("/confirmar")
def confirmar(uid: str, db: Session = Depends(get_db)):
    ok = UsuarioService.activar_correo(db, uid)

    if not ok:
        raise HTTPException(400, "UID inválido")

    return {"mensaje": "Correo verificado correctamente"}

@router.get("/verificar-correo")
def verificar_correo(uid: str, db: Session = Depends(get_db)):
    ok = UsuarioService.activar_correo(db, uid)
    if not ok:
        raise HTTPException(status_code=400, detail="No se encontró usuario con ese UID")

    return {"mensaje": "Correo verificado correctamente"}


