from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.models.administrador_model import Administrador
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
            fecha_nacimiento=data.fecha_nacimiento,
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
            )
            db.add(conductor)
        else:
            pasajero = Pasajero(id_usuario=usuario.id_usuario)
            db.add(pasajero)

        db.commit()

        # 4. Enviar correo de verificación

        # HTML Estilizado para MoveCare con tipografía como logo
        html = f"""
            <div style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f7f6; padding: 40px 20px;">
                <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">

                    <div style="background-color: #ffffff; padding: 30px 20px; text-align: center; border-bottom: 1px solid #f0f0f0;">
                        <h1 style="margin: 0; color: #1976d2; font-size: 28px; font-weight: 800; letter-spacing: 1px;">
                            MoveCare
                        </h1>
                    </div>

                    <div style="padding: 30px;">
                        <h2 style="color: #2c3e50; font-size: 22px; margin-top: 0; text-align: center;">Bienvenido</h2>
                        <p style="font-size: 16px; color: #555555; line-height: 1.6; text-align: center;">
                            Gracias por registrarte. Para poder iniciar sesión y utilizar la aplicación, necesitamos que confirmes tu correo electrónico.
                        </p>

                        <p style="font-size: 16px; color: #555555; line-height: 1.6; text-align: center; margin-top: 20px;">
                            Ingresa el siguiente código de verificación en la aplicación:
                        </p>

                        <div style="text-align: center; margin: 30px 0;">
                            <span style="display: inline-block; background-color: #e3f2fd; color: #1976d2; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 2px; border: 1px solid #bbdefb;">
                                {uid}
                            </span>
                        </div>

                        <p style="font-size: 14px; color: #777777; text-align: center; line-height: 1.5;">
                            Una vez ingresado este código, tu cuenta quedará verificada. Si no solicitaste este registro, puedes ignorar este mensaje de forma segura.
                        </p>
                    </div>

                    <div style="background-color: #f9f9f9; padding: 20px; text-align: center;">
                        <p style="font-size: 12px; color: #999999; margin: 0;">
                            © 2026 MoveCare. Todos los derechos reservados.
                        </p>
                    </div>

                </div>
            </div>
            """

        # --- AQUÍ ESTÁ LA PROTECCIÓN ---
        try:
            await EmailService.enviar_correo(
                usuario.correo,
                "Verifica tu cuenta | MoveCare",
                html
            )
        except Exception as e:
            # Si el correo falla, se imprime en Render pero la app no "crashea"
            print(f"ADVERTENCIA: Usuario guardado en BD, pero falló el envío del correo. Detalle: {str(e)}")

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
            "sub": str(usuario.id_usuario),
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

    @staticmethod
    def actualizar_perfil(db: Session, id_usuario: str, data):
        # Buscamos al usuario por su ID
        usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()

        if not usuario:
            raise Exception("Usuario no encontrado en la base de datos.")

        # Actualizamos dinámicamente solo los campos que vengan en el request
        if data.nombre_completo is not None:
            usuario.nombre_completo = data.nombre_completo
        if data.telefono is not None:
            usuario.telefono = data.telefono
        if data.direccion is not None:
            usuario.direccion = data.direccion
        if data.fecha_nacimiento is not None:
            usuario.fecha_nacimiento = data.fecha_nacimiento
        if data.foto_perfil is not None:
            usuario.foto_perfil = data.foto_perfil
        if data.discapacidad is not None:
            usuario.discapacidad = data.discapacidad

        # Guardamos los cambios
        db.commit()
        db.refresh(usuario)

        return usuario

    @staticmethod
    async def crear_admin(db: Session, data):
        # 1. Crear usuario en Firebase Auth
        uid = FirebaseAuthService.crear_usuario(data.correo, data.password)

        # 2. Crear usuario en Supabase
        usuario = Usuario(
            uid_firebase=uid,
            nombre_completo=data.nombre_completo,
            correo=data.correo,
            # Llenamos los campos obligatorios con valores dummy para que la BD no arroje error
            telefono="N/A",
            direccion="N/A",
            foto_ine="N/A",
            foto_ine_reverso="N/A",
            foto_perfil="N/A",
            rol="administrador",
            activo=True,  # Ya está activo por defecto
            autentificado=True  # Ya está verificado, no mandamos correo
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        # 3. Crear entidad Administrador
        admin = Administrador(id_usuario=usuario.id_usuario)
        db.add(admin)
        db.commit()

        # No enviamos correo. Retornamos el usuario.
        return usuario