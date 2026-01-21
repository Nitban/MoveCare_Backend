from fastapi import Depends, HTTPException, Header
from jose import jwt, JWTError
from app.core.config import settings

# ================= USUARIO ACTUAL DESDE JWT =================
def get_current_user(
    authorization: str = Header(...)
):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Token inválido")

    token = authorization.split(" ")[1]

    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
    except JWTError:
        raise HTTPException(status_code=401, detail="Token no válido o expirado")

    return {
        "id_usuario": payload.get("sub"),     # 🔥 viene del JWT
        "rol": payload.get("rol"),
        "correo": payload.get("correo"),
        "uid_firebase": payload.get("uid"),
    }


# ================= SOLO ADMIN =================
def require_admin(user=Depends(get_current_user)):
    if user["rol"] != "administrador":
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a administradores"
        )
    return user


# ================= SOLO CONDUCTOR =================
def require_conductor(user=Depends(get_current_user)):
    if user["rol"] != "conductor":
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a conductores"
        )
    return user


# ================= SOLO PASAJERO =================
def require_pasajero(user=Depends(get_current_user)):
    if user["rol"] != "pasajero":
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a pasajeros"
        )
    return user
