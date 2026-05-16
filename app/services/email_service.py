import os
import aiosmtplib
from email.message import EmailMessage

import os
import aiosmtplib
from email.message import EmailMessage


class EmailService:

    @staticmethod
    async def enviar_correo(destinatario: str, asunto: str, html: str):
        # 1. Recuperamos las variables de entorno de Render (.env)
        sender_email = os.getenv("GMAIL_SENDER_EMAIL")  # Tu correo de Gmail
        app_password = os.getenv("GMAIL_APP_PASSWORD")  # La contraseña de aplicación de 16 letras

        if not sender_email or not app_password:
            raise Exception("Error de configuración: Faltan credenciales de Gmail en el servidor.")

        # 2. Configuramos la cabecera y el cuerpo del mensaje
        msg = EmailMessage()
        msg['From'] = f"MoveCare <{sender_email}>"
        msg['To'] = destinatario
        msg['Subject'] = asunto

        # Agregamos un texto plano por defecto (requerido por buenas prácticas)
        msg.set_content("Abre este correo en un cliente que soporte HTML para ver el código de verificación.")
        # Inyectamos tu diseño HTML
        msg.add_alternative(html, subtype='html')

        # 3. Conexión SMTP asíncrona a Google
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
            raise Exception(f"Fallo en servidor SMTP de Gmail: {str(e)}")