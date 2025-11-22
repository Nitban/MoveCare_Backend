import firebase_admin
from firebase_admin import credentials, auth
import requests
import os

SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_CREDENTIALS", "firebase-adminsdk.json")

cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
firebase_admin.initialize_app(cred)


class FirebaseAuthService:

    @staticmethod
    def crear_usuario(correo: str, password: str):
        try:
            user = auth.create_user(email=correo, password=password)
            auth.generate_email_verification_link(correo)
            return user.uid
        except Exception as e:
            raise Exception(f"Error Firebase al crear usuario: {str(e)}")

    @staticmethod
    def enviar_verificacion(correo: str):
        try:
            return auth.generate_email_verification_link(correo)
        except Exception as e:
            raise Exception(f"Error al generar link de verificación: {str(e)}")

    @staticmethod
    def verificar_correo(id_token: str):
        """
        Verifica si un ID token está firmado y si el correo está verificado.
        """
        try:
            decoded = auth.verify_id_token(id_token)
            return decoded
        except Exception as e:
            raise Exception(f"Token inválido o expirado: {str(e)}")

    @staticmethod
    def validar_credenciales(correo: str, password: str):
        url = (
            f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword"
            f"?key={os.getenv('FIREBASE_API_KEY')}"
        )

        payload = {
            "email": correo,
            "password": password,
            "returnSecureToken": True
        }

        r = requests.post(url, json=payload)
        data = r.json()

        if "idToken" in data:
            return data
        else:
            raise Exception(data.get("error", {}).get("message", "Error desconocido"))

    @staticmethod
    def obtener_usuario(uid: str):
        try:
            return auth.get_user(uid)
        except Exception as e:
            raise Exception(f"Error al obtener usuario de Firebase: {str(e)}")
