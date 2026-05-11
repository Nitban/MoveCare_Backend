import os
import httpx


class EmailService:

    @staticmethod
    async def enviar_correo(destinatario: str, asunto: str, html: str):
        # 1. Recuperamos las variables de entorno
        api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL")

        # 2. Configuramos la cabecera y la URL de la API de Brevo
        url = "https://api.brevo.com/v3/smtp/email"
        headers = {
            "accept": "application/json",
            "api-key": api_key,
            "content-type": "application/json"
        }

        # 3. Armamos el cuerpo del mensaje
        payload = {
            "sender": {
                "email": sender_email,
                "name": "MoveCare"  # Nombre que verá el usuario en su bandeja
            },
            "to": [
                {"email": destinatario}
            ],
            "subject": asunto,
            "htmlContent": html
        }

        # 4. Hacemos la petición HTTP asíncrona
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)

                # Si hay un error de autenticación o validación, esto lo atrapará
                response.raise_for_status()

        except Exception as e:
            raise Exception(f"Error al enviar correo vía API de Brevo: {str(e)}")