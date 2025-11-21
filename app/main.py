from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth_route

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
app.include_router(auth_route.router, prefix="/auth", tags=["Auth"])

# ============================
# Root endpoint
# ============================
@app.get("/")
def root():
    return {"status": "MoveCare API funcionando"}


