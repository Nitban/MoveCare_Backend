from dotenv import load_dotenv
import os

load_dotenv()

class Settings:
    SUPABASE_URL: str = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    DATABASE_URL: str = os.getenv("DATABASE_URL")

    JWT_SECRET: str = os.getenv("JWT_SECRET", "supersecret")
    JWT_ALGORITHM: str = os.getenv("JWT_ALGORITHM", "HS256")
    JWT_EXP_MINUTES: int = int(os.getenv("JWT_EXP_MINUTES", 43200))  # 30 días

settings = Settings()
