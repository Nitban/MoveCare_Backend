from pydantic import BaseModel, EmailStr
from typing import Optional


class RegistroBase(BaseModel):
    nombre_completo: str
    correo: EmailStr
    telefono: str
    password: str
    # Campos que el front NO envía en el registro inicial
    edad: Optional[int] = None
    direccion: Optional[str] = None
    discapacidad: Optional[str] = None
    foto_ine_base64: Optional[str] = None


class RegistroPasajero(RegistroBase):
    rol: str = "pasajero"


class RegistroConductor(RegistroBase):
    rol: str = "conductor"
    licencia_base64: Optional[str] = None


class LoginSchema(BaseModel):
    correo: EmailStr
    password: str


class LoginResponse(BaseModel):
    mensaje: str
    access_token: Optional[str] = None
    token_type: str = "bearer"
    id_usuario: Optional[str] = None


class VerifyEmailRequest(BaseModel):
    id_token: str
