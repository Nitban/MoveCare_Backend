from pydantic import BaseModel, EmailStr

class UsuarioRegistro(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    tipo_usuario: str  # pasajero / conductor / admin

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

