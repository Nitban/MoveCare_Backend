from fastapi import Depends, HTTPException
from app.core.security import get_current_user

def require_admin(user=Depends(get_current_user)):
    if user["rol"] != "administrador":
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a administradores"
        )
    return user

def require_conductor(user=Depends(get_current_user)):
    if user["rol"] != "conductor":
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a conductores"
        )
    return user

def require_pasajero(user=Depends(get_current_user)):
    if user["rol"] != "pasajero":
        raise HTTPException(
            status_code=403,
            detail="Acceso restringido a pasajeros"
        )
    return user
