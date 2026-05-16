import os
import httpx


class EmailService:

    @staticmethod
    async def enviar_correo(destinatario: str, asunto: str, html: str):
        # 1. Recuperamos las variables de entorno
        api_key = os.getenv("BREVO_API_KEY")
        sender_email = os.getenv("BREVO_SENDER_EMAIL")

        if not api_key or not sender_email:
            raise Exception("Faltan las variables de entorno de Brevo en Render.")

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
            # timeout=10.0 asegura que si Brevo está lento, no congele tu backend
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(url, json=payload, headers=headers)

                # Si Brevo rechaza el correo (ej. API Key mala), extraemos su mensaje
                if response.status_code != 201 and response.status_code != 200:
                    error_msg = response.json().get("message", "Error desconocido en Brevo")
                    raise Exception(f"Brevo rechazó la petición: {error_msg}")

        except httpx.RequestError as e:
            raise Exception(f"Error de red al intentar conectar con Brevo: {str(e)}")