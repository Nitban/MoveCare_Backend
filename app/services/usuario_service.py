from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.services.firebase_service import FirebaseAuthService
from app.core.security import crear_jwt
from app.services.email_service import EmailService
import os

class UsuarioService:

    @staticmethod
    async def crear_usuario(db: Session, data, is_conductor=False):

        # 1. Crear usuario en Firebase Auth
        uid = FirebaseAuthService.crear_usuario(data.correo, data.password)

        # 2. Crear usuario en Supabase
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
            activo=False,  # Admin debe aprobar
            autentificado=False  # Correo aún no verificado
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # 3. Crear perfil adicional
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

        # 4. Enviar correo de verificación
        #link = f"{os.getenv('FRONTEND_URL')}/confirmar-correo?uid={uid}"
        link = f"http://localhost:55308/#/confirmar-correo?uid={uid}"

        html = f"""
        <div style="font-family: Arial, sans-serif; max-width: 480px; margin: auto; padding: 20px;
                    border-radius: 12px; background: #ffffff; border: 1px solid #e0e0e0;">

            <h2 style="color: #4A4A4A; text-align: center;">
                Bienvenido a MoveCare 🚗💙
            </h2>

            <p style="font-size: 15px; color: #333;">
                Gracias por registrarte en <b>MoveCare</b>.
                Para poder iniciar sesión, necesitamos que confirmes tu correo electrónico.
            </p>

            <p style="font-size: 15px; color: #333;">
                Ingresa el siguiente <b>código de verificación</b> en la pantalla de
                <b>Confirmar correo</b> dentro de la aplicación:
            </p>

            <div style="text-align: center; margin: 25px 0;">
                <span style="
                    display: inline-block;
                    background-color: #f5f5f5;
                    padding: 12px 20px;
                    border-radius: 8px;
                    font-size: 16px;
                    font-weight: bold;
                    color: #007BFF;
                    letter-spacing: 1px;
                ">
                    {uid}
                </span>
            </div>

            <p style="font-size: 14px; color: #555;">
                Una vez ingresado este código, tu correo quedará verificado y
                podrás iniciar sesión normalmente.
            </p>

            <p style="font-size: 14px; color: #555;">
                Si tú no creaste esta cuenta, puedes ignorar este mensaje.
            </p>

            <hr style="margin: 25px 0; border: none; border-top: 1px solid #ddd;">

            <p style="font-size: 12px; text-align: center; color: #888;">
                © 2025 MoveCare. Todos los derechos reservados.
            </p>
        </div>
        """

        await EmailService.enviar_correo(
            usuario.correo,
            "Verifica tu cuenta | MoveCare",
            html
        )

        return usuario

    @staticmethod
    def login(db: Session, correo: str, password: str):

        try:
            cred = FirebaseAuthService.validar_credenciales(correo, password)
        except Exception as e:
            return None, f"Error Firebase: {str(e)}", None

        uid = cred.get("localId")

        usuario = db.query(Usuario).filter(Usuario.uid_firebase == uid).first()

        if not usuario:
            return None, "Usuario no encontrado en Supabase.", None

        if not usuario.autentificado:
            return None, "Debes verificar tu correo antes de iniciar sesión.", None

        ##if not usuario.activo:
          ##  return None, "Tu cuenta aún no ha sido aprobada por los administradores."

        payload = {
            "sub": str(usuario.id_usuario),  # 🔥 FIX
            "uid": usuario.uid_firebase,
            "correo": usuario.correo,
            "rol": usuario.rol
        }

        token = crear_jwt(payload)

        return token, "Login exitoso.", usuario.rol

    @staticmethod
    def obtener_id_conductor_por_usuario(db: Session, id_usuario):
        conductor = (
            db.query(Conductor)
            .filter(Conductor.id_usuario == id_usuario)
            .first()
        )

        if not conductor:
            return None

        return conductor.id_conductor

    @staticmethod
    def confirmar_correo(db: Session, uid_firebase: str):
        usuario = (
            db.query(Usuario)
            .filter(Usuario.uid_firebase == uid_firebase)
            .first()
        )

        if not usuario:
            return False, "UID inválido"

        if usuario.autentificado:
            return True, "El correo ya estaba verificado"

        usuario.autentificado = True
        db.commit()

        return True, "Correo verificado correctamente"
