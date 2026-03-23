from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.dependencies.auth_dependencies import require_pasajero, require_conductor, require_admin
from app.services.app_service import AppService

router = APIRouter(
    prefix="/home",
    tags=["Home"]
)


# ================= HOME ADMINISTRADOR =================
@router.get("/home/administrador")
def home_administrador(
        db: Session = Depends(get_db),
        administrador=Depends(require_admin)
):
    # 1. Imprimimos en la consola del servidor qué trae exactamente "administrador"
    print("👉 DATOS DEL ADMIN DESDE EL TOKEN:", administrador)

    # 2. Extraemos el ID (como vimos en tu log, extraerá 'id_usuario')
    admin_id = administrador.get("id_administrador") or administrador.get("id_usuario") or administrador.get("id")

    # 3. Validamos por si acaso
    if not admin_id:
        raise HTTPException(status_code=500, detail="No se pudo encontrar el ID del administrador en el token.")

    # 4. LLAMADA CORREGIDA: Usamos el nuevo nombre del parámetro (id_usuario)
    return AppService.get_home_administrador(
        db=db,
        id_usuario=admin_id  # <--- ESTE ES EL ÚNICO CAMBIO
    )

# ================= HOME PASAJERO =================
@router.get("/home/pasajero")
def home_pasajero(
    db: Session = Depends(get_db),
    user=Depends(require_pasajero)
):
    return AppService.get_home_pasajero(
        db=db,
        id_usuario=user["id_usuario"]
    )

# ================= HOME CONDUCTOR =================
@router.get("/home/conductor")
def home_conductor(
    db: Session = Depends(get_db),
    user=Depends(require_conductor)
):
    return AppService.get_home_conductor(
        db=db,
        id_usuario=user["id_usuario"]
    )

