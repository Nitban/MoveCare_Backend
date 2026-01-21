from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegistroPasajero, RegistroConductor, LoginSchema
from app.schemas.confirmarCorreo import ConfirmarCorreoRequest
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/registro/pasajero")
async def registrar_pasajero(data: RegistroPasajero, db: Session = Depends(get_db)):
    try:
        usuario = await UsuarioService.crear_usuario(db, data, is_conductor=False)
        return {
            "mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta.",
            "id_usuario": usuario.id_usuario
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/registro/conductor")
async def registrar_conductor(data: RegistroConductor, db: Session = Depends(get_db)):
    try:
        usuario = await UsuarioService.crear_usuario(db, data, is_conductor=True)
        return {
            "mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta.",
            "id_usuario": usuario.id_usuario
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    token, msg, rol = UsuarioService.login(db, data.correo, data.password)

    if token is None:
        raise HTTPException(status_code=401, detail=msg)

    print(msg)
    return {
        "mensaje": msg,
        "token": token,
        "rol": rol
    }

@router.post("/confirmar-correo")
def confirmar_correo(
    data: ConfirmarCorreoRequest,
    db: Session = Depends(get_db)
):
    ok = UsuarioService.confirmar_correo(db, data.uid)

    if not ok:
        raise HTTPException(
            status_code=400,
            detail="UID inválido o usuario no encontrado"
        )

    return {"mensaje": "Correo verificado correctamente"}
