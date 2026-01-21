from pydantic import BaseModel

class ConfirmarCorreoRequest(BaseModel):
    uid: str
