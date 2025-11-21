from pydantic import BaseModel, EmailStr
from typing import Optional


class RegistroBase(BaseModel):
    nombre_completo: str
    edad: int
    direccion: str
    telefono: str
    correo: EmailStr
    discapacidad: Optional[str] = None
    rol: str                         # pasajero / conductor
    password: str
    foto_ine_base64: str


class RegistroPasajero(RegistroBase):
    pass


class RegistroConductor(RegistroBase):
    licencia_base64: str


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
