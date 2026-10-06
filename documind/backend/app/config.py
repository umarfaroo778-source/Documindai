import os
from pydantic_settings import BaseSettings

is_vercel = bool(os.getenv("VERCEL"))
default_db = "sqlite:////tmp/documind.db" if is_vercel else "sqlite:///./documind.db"
default_upload = "/tmp/uploads" if is_vercel else "./uploads"

class Settings(BaseSettings):
    APP_NAME: str = "DocuMind"
    APP_ENV: str = "development"
    SECRET_KEY: str = "documind-secret-key-super-secure-university-project-2026"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440 # 24 hours

    DATABASE_URL: str = default_db
    UPLOAD_DIR: str = default_upload

    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

try:
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
except Exception:
    pass

