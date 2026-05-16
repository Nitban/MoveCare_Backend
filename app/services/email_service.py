import os
import aiosmtplib
from email.message import EmailMessage


class EmailService:

    @staticmethod
    async def enviar_correo(destinatario: str, asunto: str, html: str):
        # 1. Recuperamos las variables de entorno de Gmail
        sender_email = os.getenv("GMAIL_SENDER_EMAIL")
        app_password = os.getenv("GMAIL_APP_PASSWORD")

        if not sender_email or not app_password:
            raise Exception("Error de configuración: Faltan credenciales de Gmail.")

        # 2. Configuramos la cabecera y el cuerpo del mensaje
        msg = EmailMessage()
        # El formato "Nombre <correo>" hace que en la bandeja de entrada diga "MoveCare"
        msg['From'] = f"MoveCare <{sender_email}>"
        msg['To'] = destinatario
        msg['Subject'] = asunto

        # Agregamos un texto plano por defecto (requerido por buenas prácticas)
        msg.set_content("Tu cliente de correo no soporta mensajes HTML.")
        # Inyectamos el HTML estilizado que armas en el UsuarioService
        msg.add_alternative(html, subtype='html')

        # 3. Hacemos la conexión SMTP asíncrona a los servidores de Google
        try:
            await aiosmtplib.send(
                msg,
                hostname="smtp.gmail.com",
                port=587,
                start_tls=True,
                username=sender_email,
                password=app_password
            )
        except Exception as e:
            # Atrapa errores como contraseñas inválidas o bloqueos de Google
            raise Exception(f"Error al enviar correo vía Gmail: {str(e)}")