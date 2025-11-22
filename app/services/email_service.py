import os
import aiosmtplib
from email.message import EmailMessage


class EmailService:

    @staticmethod
    async def enviar_correo(destinatario: str, asunto: str, html: str):
        mensaje = EmailMessage()
        mensaje["From"] = os.getenv("BREVO_SENDER_EMAIL")
        mensaje["To"] = destinatario
        mensaje["Subject"] = asunto
        mensaje.set_content("Tu cliente de correo no soporta HTML.")
        mensaje.add_alternative(html, subtype="html")

        try:
            await aiosmtplib.send(
                mensaje,
                hostname=os.getenv("BREVO_SMTP_SERVER"),
                port=int(os.getenv("BREVO_SMTP_PORT")),
                username=os.getenv("BREVO_SMTP_USERNAME"),
                password=os.getenv("BREVO_SMTP_PASSWORD"),
                start_tls=True
            )
        except Exception as e:
            raise Exception(f"Error al enviar correo SMTP: {str(e)}")
