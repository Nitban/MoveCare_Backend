from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.services.firebase_service import FirebaseAuthService
from app.core.security import crear_jwt


class UsuarioService:

    @staticmethod
    def crear_usuario(db: Session, data, is_conductor=False):

        # Crear usuario en Firebase
        uid = FirebaseAuthService.crear_usuario(data.correo, data.password)

        # Guardar INE como base64 directamente
        usuario = Usuario(
            uid_firebase=uid,
            nombre_completo=data.nombre_completo,
            edad=data.edad,
            direccion=data.direccion,
            correo=data.correo,
            telefono=data.telefono,
            discapacidad=data.discapacidad,
            rol=data.rol,
            foto_ine=data.foto_ine_base64,
            activo=False
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # Crear perfil adicional
        if is_conductor:
            conductor = Conductor(
                id_usuario=usuario.id_usuario,
                licencia_conduccion=data.licencia_base64
            )
            db.add(conductor)

        else:
            pasajero = Pasajero(id_usuario=usuario.id_usuario)
            db.add(pasajero)

        db.commit()

        return usuario

    @staticmethod
    def activar_correo(db: Session, uid_firebase: str):
        usuario = db.query(Usuario).filter(Usuario.uid_firebase == uid_firebase).first()
        if usuario:
            usuario.autentificado = True
            db.commit()
            return True
        return False

    @staticmethod
    def login(db: Session, correo: str, password: str):

        try:
            cred = FirebaseAuthService.validar_credenciales(correo, password)
        except Exception as e:
            return None, f"Error Firebase: {str(e)}"

        uid = cred.get("localId")

        # Validar email verificado
        firebase_user = FirebaseAuthService.obtener_usuario(uid)
        if not firebase_user.email_verified:
            return None, "Correo no verificado."

        # Activar correo verificado
        UsuarioService.activar_correo(db, uid)

        # Validar existencia en BD
        usuario = db.query(Usuario).filter(Usuario.uid_firebase == uid).first()
        if not usuario:
            return None, "Usuario no encontrado en Supabase."

        if not usuario.autentificado:
            return None, "Correo no verificado."

        if not usuario.activo:
            return None, "Tu cuenta aún no ha sido aprobada por los administradores."

        token = crear_jwt({
            "id_usuario": str(usuario.id_usuario),
            "rol": usuario.rol
        })

        return token, "Login exitoso."
