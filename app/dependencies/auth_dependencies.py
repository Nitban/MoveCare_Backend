from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from app.core.config import settings
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.usuario_model import Usuario

# Obtener usuario actual desde el token JWT
def get_current_user(
    authorization: str = Header(...),
    db: Session = Depends(get_db)
):

    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.split(" ")[1]

    try:
        data = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token no válido o expirado")

    id_usuario = data.get("id_usuario")

    usuario = db.query(Usuario).filter(Usuario.id == id_usuario).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    return usuario

# Dependencia: SOLO ADMINISTRADORES
def require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.tipo_usuario != "administrador":
        raise HTTPException(status_code=403, detail="Acceso restringido a administradores")
    return current_user

# Dependencia: SOLO CHOFER
def require_conductor(current_user: Usuario = Depends(get_current_user)):
    if current_user.tipo_usuario != "conductor":
        raise HTTPException(status_code=403, detail="Acceso restringido a conductores")
    return current_user

# Dependencia: SOLO PASAJERO
def require_pasajero(current_user: Usuario = Depends(get_current_user)):
    if current_user.tipo_usuario != "pasajero":
        raise HTTPException(status_code=403, detail="Acceso restringido a pasajeros")
    return current_user
