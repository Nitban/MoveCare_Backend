from datetime import datetime, timedelta
from jose import jwt
from app.core.config import settings

def crear_jwt(payload: dict):
    exp = datetime.utcnow() + timedelta(minutes=settings.JWT_EXP_MINUTES)
    token_data = {
        **payload,
        "exp": exp,
        "iat": datetime.utcnow(),
        "iss": "movecare-backend"
    }
    return jwt.encode(
        token_data,
        settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

def verificar_jwt(token: str):
    try:
        data = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )
        return data
    except Exception:
        return None

