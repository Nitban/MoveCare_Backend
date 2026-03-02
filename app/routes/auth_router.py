from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegistroPasajero, RegistroConductor, LoginSchema, UsuarioUpdate
from app.schemas.confirmarCorreo import ConfirmarCorreoRequest
from app.services.usuario_service import UsuarioService
from app.core.security import get_current_user

from app.schemas.validacion import ValidacionUsuarioCreate, ValidacionUsuarioResponse
from app.services.validacion_service import ValidacionService

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


# Agrega esta ruta al final de tus rutas de Auth
@router.post("/logout")
def logout(db: Session = Depends(get_db)):
    # Al usar JWT, no hay una sesión física que destruir en la BD.
    # En el futuro, aquí puedes agregar lógica para meter el token en una "lista negra" (Redis/DB)
    # o usar FirebaseAuthService.revocar_tokens(uid) si necesitas forzar el cierre en todos los dispositivos.

    return {
        "mensaje": "Sesión cerrada correctamente en el servidor."
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

@router.post("/validacion", response_model=ValidacionUsuarioResponse)
def subir_documentos_ine(
    data: ValidacionUsuarioCreate,
    db: Session = Depends(get_db),
    user = Depends(get_current_user)
):
    try:
        return ValidacionService.crear_validacion(db, user["id_usuario"], data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.put("/actualizar-perfil")
def actualizar_perfil(
        data: UsuarioUpdate,
        db: Session = Depends(get_db),
        user=Depends(get_current_user)  # Obtenemos el usuario del token
):
    try:
        # user["id_usuario"] viene del token JWT
        UsuarioService.actualizar_perfil(db, user["id_usuario"], data)

        return {
            "mensaje": "Perfil actualizado correctamente"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))