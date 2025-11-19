from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.services.firebase_service import FirebaseAuthService
from app.services.storage_service import StorageService
from app.core.security import crear_jwt


class UsuarioService:

    # -------------------------------------------------------
    # Crear usuario completo
    # -------------------------------------------------------
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
            activo=False   # Se activará tras verificar correo
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # Crear perfil adicional
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

    # -------------------------------------------------------
    # Activar usuario luego de verificar correo
    # -------------------------------------------------------
    @staticmethod
    def activar_usuario(db: Session, uid_firebase: str):
        usuario = db.query(Usuario).filter(Usuario.uid_firebase == uid_firebase).first()
        if usuario:
            usuario.activo = True
            db.commit()
            return True
        return False

    # -------------------------------------------------------
    # Login
    # -------------------------------------------------------
    @staticmethod
    def login(db: Session, correo: str, password: str):

        # 1. Validar credenciales con Firebase (REST)
        datos = FirebaseAuthService.validar_credenciales(correo, password)
        if not datos:
            return None, "Correo o contraseña incorrectos."

        uid = datos["localId"]

        # 2. Validar si el email está verificado
        usuario_firebase = FirebaseAuthService.obtener_usuario(uid)
        if not usuario_firebase.email_verified:
            return None, "Correo no verificado. Revisa tu bandeja."

        # 3. Activar en BD si procede
        UsuarioService.activar_usuario(db, uid)

        # 4. Traer usuario local
        usuario = db.query(Usuario).filter(Usuario.uid_firebase == uid).first()
        if not usuario:
            return None, "Usuario no encontrado en la Base de Datos."

        if usuario.activo is False:
            return None, "Cuenta aún no activa."

        # 5. Generar token interno
        token = crear_jwt({
            "id_usuario": usuario.id,
            "tipo_usuario": usuario.tipo_usuario
        })

        return token, "Login exitoso."
