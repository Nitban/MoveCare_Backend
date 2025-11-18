from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.services.firebase_service import FirebaseAuthService
from app.services.storage_service import StorageService
from app.core.security import crear_jwt

class UsuarioService:

    @staticmethod
    def crear_usuario(db: Session, data, is_conductor=False):

        # Crear usuario en Firebase
        uid = FirebaseAuthService.crear_usuario(data.correo, data.password)

        # Subir INE
        ine_url = StorageService.subir_imagen(data.foto_ine_base64, "ine")

        usuario = Usuario(
            uid_firebase=uid,
            nombre_completo=data.nombre_completo,
            edad=data.edad,
            direccion=data.direccion,
            telefono=data.telefono,
            correo=data.correo,
            discapacidad=data.discapacidad,
            tipo_usuario=data.tipo_usuario,
            foto_ine_url=ine_url,
            activo=False
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # Crear perfil correspondiente
        if is_conductor:
            licencia_url = StorageService.subir_imagen(data.licencia_base64, "licencias")

            conductor = Conductor(
                id_usuario=usuario.id,
                licencia_url=licencia_url
            )
            db.add(conductor)

        else:
            pasajero = Pasajero(id_usuario=usuario.id)
            db.add(pasajero)

        db.commit()

        return usuario

    @staticmethod
    def activar_usuario(db: Session, uid_firebase: str):
        usuario = db.query(Usuario).filter(Usuario.uid_firebase == uid_firebase).first()
        if usuario:
            usuario.activo = True
            db.commit()
            return True
        return False

    @staticmethod
    def login(db: Session, correo: str, password: str):
        datos = FirebaseAuthService.validar_credenciales(correo, password)
        if not datos:
            return None, "Correo o contraseña incorrectos."

        uid = datos["localId"]

        # validar que está verificado
        usuario_firebase = FirebaseAuthService.obtener_usuario(uid)
        if not usuario_firebase.email_verified:
            return None, "Correo no verificado."

        # activar en Supabase
        UsuarioService.activar_usuario(db, uid)

        # verificar si existe en BD
        usuario = db.query(Usuario).filter(Usuario.uid_firebase == uid).first()
        if not usuario:
            return None, "Usuario no encontrado en BD."

        if usuario.activo is False:
            return None, "Cuenta aún no activa."

        # Generar token interno
        token = crear_jwt(usuario.id)

        return token, "Login exitoso."