from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.schemas.auth import RegistroPasajero, RegistroConductor, LoginSchema
from app.services.usuario_service import UsuarioService

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/registro/pasajero")
def registrar_pasajero(data: RegistroPasajero, db: Session = Depends(get_db)):
    try:
        UsuarioService.crear_usuario(db, data, is_conductor=False)
        return {"mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/registro/conductor")
def registrar_conductor(data: RegistroConductor, db: Session = Depends(get_db)):
    try:
        UsuarioService.crear_usuario(db, data, is_conductor=True)
        return {"mensaje": "Registro exitoso. Revisa tu correo para verificar tu cuenta."}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login")
def login(data: LoginSchema, db: Session = Depends(get_db)):
    token, msg = UsuarioService.login(db, data.correo, data.password)
    if token is None:
        raise HTTPException(status_code=401, detail=msg)
    return {"mensaje": msg, "token": token}

#@router.post("/verificar-correo")
#def verificar_correo(data: VerifyEmailRequest, db: Session = Depends(get_db)):
 #   verificado, uid = FirebaseAuthService.verificar_email(data.id_token)

  #  if not verificado:
   #     raise HTTPException(
    #        status_code=400,
      #      detail="Correo aún no verificado en Firebase."
     #   )

    # Activar en BD
    #UsuarioService.activar_usuario(db, uid)

    #return {"mensaje": "Correo verificado y usuario activado correctamente."}

