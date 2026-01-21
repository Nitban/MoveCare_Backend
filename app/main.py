from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import app.models
from app.core.database import engine, Base
from sqlalchemy.orm import configure_mappers
from app.routes import auth_router, vehiculo_router, usuario_router, app_router, viajes_router

try:
    configure_mappers()
except Exception as e:
    print(f"Error configurando mappers: {e}")

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="MoveCare Backend",
    version="1.0.0",
    debug=True
)

# ============================
# CORS
# ============================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================
# Routers
# ============================

app.include_router(app_router.router, prefix="/app", tags=["Home"])
app.include_router(auth_router.router, prefix="/auth", tags=["Auth"])
app.include_router(vehiculo_router.router, prefix="/register", tags=["Vehiculos"])
app.include_router(usuario_router.router, prefix="/users", tags=["Usuarios"])
app.include_router(viajes_router.router)

# ============================
# Root endpoint
# ============================
@app.get("/")
def root():
    return {"status": "MoveCare API funcionando"}


