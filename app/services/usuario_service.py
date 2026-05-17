from sqlalchemy.orm import Session
from app.models.usuario_model import Usuario
from app.models.pasajero_model import Pasajero
from app.models.conductor_model import Conductor
from app.models.administrador_model import Administrador
from app.services.firebase_service import FirebaseAuthService
from app.core.security import crear_jwt
from app.services.email_service import EmailService
import random
from datetime import datetime, timedelta


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
            activo=False,
            autentificado=False
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

        # --- AQUÍ EXTRAEMOS LOS ÚLTIMOS 4 CARACTERES ---
        codigo_corto = uid[-4:]

        # 4. Enviar correo de verificación
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
                                {codigo_corto}
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

        try:
            await EmailService.enviar_correo(
                usuario.correo,
                "Verifica tu cuenta | MoveCare",
                html
            )
        except Exception as e:
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
    def confirmar_correo(db: Session, codigo_corto: str):
        usuario = (
            db.query(Usuario)
            .filter(Usuario.uid_firebase.endswith(codigo_corto))
            .first()
        )

        if not usuario:
            return False, "Código inválido"

        if usuario.autentificado:
            return True, "El correo ya estaba verificado"

        usuario.autentificado = True
        db.commit()

        return True, "Correo verificado correctamente"

    @staticmethod
    def actualizar_perfil(db: Session, id_usuario: str, data):
        usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()

        if not usuario:
            raise Exception("Usuario no encontrado en la base de datos.")

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

        db.commit()
        db.refresh(usuario)

        return usuario

    @staticmethod
    async def crear_admin(db: Session, data):
        uid = FirebaseAuthService.crear_usuario(data.correo, data.password)

        usuario = Usuario(
            uid_firebase=uid,
            nombre_completo=data.nombre_completo,
            correo=data.correo,
            telefono="N/A",
            direccion="N/A",
            foto_ine="N/A",
            foto_ine_reverso="N/A",
            foto_perfil="N/A",
            rol="administrador",
            activo=True,
            autentificado=True
        )

        db.add(usuario)
        db.commit()
        db.refresh(usuario)

        admin = Administrador(id_usuario=usuario.id_usuario)
        db.add(admin)
        db.commit()

        return usuario

    # ==========================================
    # NUEVAS FUNCIONES DE RECUPERACIÓN DE CLAVE
    # ==========================================

    @staticmethod
    async def solicitar_recuperacion(db: Session, correo: str):
        usuario = db.query(Usuario).filter(Usuario.correo == correo).first()
        if not usuario:
            return False, "No existe una cuenta con este correo."

        # Generar código aleatorio de 4 dígitos (ej. 0492)
        codigo = f"{random.randint(0, 9999):04d}"

        # Guardar en BD con expiración de 15 minutos
        usuario.reset_codigo = codigo
        usuario.reset_expiracion = datetime.utcnow() + timedelta(minutes=15)
        db.commit()

        # HTML Estilizado para la recuperación
        html = f"""
        <div style="font-family: 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f4f7f6; padding: 40px 20px;">
            <div style="max-width: 500px; margin: 0 auto; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 10px rgba(0,0,0,0.05);">

                <div style="background-color: #ffffff; padding: 30px 20px; text-align: center; border-bottom: 1px solid #f0f0f0;">
                    <h1 style="margin: 0; color: #1976d2; font-size: 28px; font-weight: 800; letter-spacing: 1px;">
                        MoveCare
                    </h1>
                </div>

                <div style="padding: 30px;">
                    <h2 style="color: #2c3e50; font-size: 22px; margin-top: 0; text-align: center;">Recuperación de Contraseña</h2>
                    <p style="font-size: 16px; color: #555555; line-height: 1.6; text-align: center;">
                        Hemos recibido una solicitud para restablecer la contraseña de tu cuenta.
                    </p>

                    <p style="font-size: 16px; color: #555555; line-height: 1.6; text-align: center; margin-top: 20px;">
                        Ingresa el siguiente código de seguridad en la aplicación:
                    </p>

                    <div style="text-align: center; margin: 30px 0;">
                        <span style="display: inline-block; background-color: #e3f2fd; color: #1976d2; padding: 15px 30px; border-radius: 8px; font-size: 24px; font-weight: bold; letter-spacing: 2px; border: 1px solid #bbdefb;">
                            {codigo}
                        </span>
                    </div>

                    <p style="font-size: 14px; color: #e53935; text-align: center; line-height: 1.5; font-weight: bold;">
                        Este código expirará en 15 minutos.
                    </p>

                    <p style="font-size: 14px; color: #777777; text-align: center; line-height: 1.5; margin-top: 20px;">
                        Si no solicitaste un cambio de contraseña, ignora este correo. Tu cuenta sigue estando segura.
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
        try:
            await EmailService.enviar_correo(correo, "Recupera tu contraseña | MoveCare", html)
        except Exception as e:
            print(f"Error al enviar correo de recuperación: {e}")
            return False, "Error al enviar el correo."

        return True, "Código enviado exitosamente."

    @staticmethod
    def validar_codigo_recuperacion(db: Session, correo: str, codigo: str):
        usuario = db.query(Usuario).filter(Usuario.correo == correo).first()

        if not usuario or not usuario.reset_codigo:
            return False, "Solicitud inválida."

        if usuario.reset_codigo != codigo:
            return False, "El código es incorrecto."

        if datetime.utcnow() > usuario.reset_expiracion:
            return False, "El código ha expirado. Solicita uno nuevo."

        return True, "Código válido."

    @staticmethod
    def cambiar_password(db: Session, correo: str, codigo: str, nueva_password: str):
        es_valido, msj = UsuarioService.validar_codigo_recuperacion(db, correo, codigo)
        if not es_valido:
            return False, msj

        usuario = db.query(Usuario).filter(Usuario.correo == correo).first()

        # Cambiamos la contraseña en Firebase
        try:
            FirebaseAuthService.cambiar_password(usuario.uid_firebase, nueva_password)
        except Exception as e:
            return False, f"Error en Firebase: {str(e)}"

        # Limpiamos las columnas para que el código no se pueda reutilizar
        usuario.reset_codigo = None
        usuario.reset_expiracion = None
        db.commit()

        return True, "Contraseña actualizada correctamente."