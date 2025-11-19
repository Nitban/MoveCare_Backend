import os
import requests
import firebase_admin
from firebase_admin import credentials, auth

SERVICE_ACCOUNT_PATH = os.getenv("FIREBASE_CREDENTIALS", "firebase_key.json")

if not firebase_admin._apps:
    cred = credentials.Certificate(SERVICE_ACCOUNT_PATH)
    firebase_admin.initialize_app(cred)


class FirebaseAuthService:

    # --------------------------------------------------
    # Crear usuario en Firebase Authentication
    # --------------------------------------------------
    @staticmethod
    def crear_usuario(correo: str, password: str):
        user = auth.create_user(email=correo, password=password)
        # no enviamos verificación aquí porque la app enviará el link cuando lo requieras
        return user.uid

    # --------------------------------------------------
    # Generar link de verificación
    # --------------------------------------------------
    @staticmethod
    def enviar_verificacion(correo: str):
        link = auth.generate_email_verification_link(correo)
        return link

    # --------------------------------------------------
    # Verificar token ID devuelto por Firebase
    # --------------------------------------------------
    @staticmethod
    def verificar_token(token: str):
        return auth.verify_id_token(token)

    # --------------------------------------------------
    # Obtener usuario por UID
    # --------------------------------------------------
    @staticmethod
    def obtener_usuario(uid: str):
        return auth.get_user(uid)

    # --------------------------------------------------
    # Validar Credenciales
    # --------------------------------------------------
    @staticmethod
    def validar_credenciales(correo: str, password: str):
        """
        Firebase Admin **NO** puede hacer login.
        Por eso hacemos login usando el endpoint oficial REST.
        """
        FIREBASE_API_KEY = os.getenv("FIREBASE_API_KEY")
        if not FIREBASE_API_KEY:
            raise Exception("Faltó configurar FIREBASE_API_KEY en el .env")

        url = f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}"

        payload = {
            "email": correo,
            "password": password,
            "returnSecureToken": True
        }

        r = requests.post(url, json=payload)

        if r.status_code != 200:
            return None

        data = r.json()

        if "idToken" in data:
            return data

        return None
