import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

class FirebaseAuthService:

    @staticmethod
    def crear_usuario(correo: str, password: str):
        user = auth.create_user(email=correo, password=password)
        auth.generate_email_verification_link(correo)
        return user.uid

    @staticmethod
    def enviar_verificacion(correo: str):
        link = auth.generate_email_verification_link(correo)
        return link

    @staticmethod
    def verificar_token(token: str):
        return auth.verify_id_token(token)

    @staticmethod
    def obtener_usuario(uid: str):
        return auth.get_user(uid)

    @staticmethod
    def validar_credenciales(correo: str, password: str):
        """
        Firebase Admin NO permite login directo,
        así que se valida vía REST API oficial de Firebase.
        """
        import requests
        import os

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={os.getenv('FIREBASE_API_KEY')}"

        payload = {
            "email": correo,
            "password": password,
            "returnSecureToken": True
        }

        r = requests.post(url, json=payload)
        data = r.json()

        if "idToken" in data:
            return data
        return None