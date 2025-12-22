Sistema backend para la plataforma móvil MoveCare, orientada a transporte accesible para personas con discapacidad y adultos mayores. 
Este servicio gestiona el registro, autenticación, verificación de usuarios y almacenamiento seguro en la base de datos.

🚀 Tecnologías utilizadas
Python 3.12+
FastAPI – Framework para el backend
Uvicorn – Servidor ASGI
SQLAlchemy – ORM para la base de datos
Supabase PostgreSQL – Base de datos principal
Firebase Authentication – Autenticación de usuarios
Brevo SMTP – Envío de correos de verificación
Python-dotenv – Manejo de variables de entorno

MoveCare_Back/
│── app/
│   ├── routers/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   ├── core/
│   └── main.py
│
├── requirements.txt
├── .env
└── README.md

🔧 Requisitos previos
Antes de ejecutar el proyecto asegúrate de tener:
Python 3.12 instalado
Una base de datos Supabase creada
Configuración de Firebase (clave AdminSDK)
Credenciales SMTP de Brevo
Entorno virtual configurado opcionalmente

⚙️ Instalación
Clonar el repositorio:
git clone <URL-del-repositorio>

Crear entorno virtual:
python -m venv .venv

Activarlo:
.venv\Scripts\activate

Instalar dependencias:
pip install -r requirements.txt

Ejecutar el servidor
uvicorn app.main:app --reload

Abrir la documentación interactiva:
👉 http://127.0.0.1:8000/docs

🧪 Endpoints principales
POST /auth/registro/pasajero
POST /auth/registro/conductor
POST /auth/login
GET /auth/confirmar-correo (pendiente de implementación según flujo móvil)
