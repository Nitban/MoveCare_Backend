import base64
from firebase_admin import storage
import uuid

class StorageService:

    @staticmethod
    def subir_imagen(base64_img: str, carpeta: str):
        bucket = storage.bucket()
        nombre_archivo = f"{carpeta}/{uuid.uuid4()}.jpg"
        blob = bucket.blob(nombre_archivo)

        imagen_bytes = base64.b64decode(base64_img)
        blob.upload_from_string(imagen_bytes, content_type="image/jpeg")

        blob.make_public()
        return blob.public_url
