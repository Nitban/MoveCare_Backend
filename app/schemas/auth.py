from pydantic import BaseModel, EmailStr
from typing import Optional

class RegistroBase(BaseModel):
    nombre_completo: str
    edad: int
    direccion: str
    telefono: str
    correo: EmailStr
    discapacidad: Optional[str] = None
    tipo_usuario: str  # pasajero o conductor
    password: str

class RegistroPasajero(RegistroBase):
    foto_ine_base64: str  # imagen en base64

class RegistroConductor(RegistroBase):
    foto_ine_base64: str
    licencia_base64: str
    vehiculo_marca: str
    vehiculo_modelo: str
    vehiculo_color: str
    vehiculo_placas: str

class LoginSchema(BaseModel):
    correo: EmailStr
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    id_usuario: Optional[int] = None
    mensaje: Optional[str] = None

class VerifyEmailRequest(BaseModel):
    id_token: str