from pydantic import BaseModel, EmailStr
from uuid import UUID

class UsuarioRegistro(BaseModel):
    nombre: str
    email: EmailStr
    password: str
    rol: str  # pasajero / conductor / admin

class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

class ConductorIdResponse(BaseModel):
    id_conductor: UUID