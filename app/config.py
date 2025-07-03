from pydantic_settings import BaseSettings
from typing import Optional, List
import os


class Settings(BaseSettings):
    # Database settings
    database_url: str = os.getenv("DATABASE_URL", "postgresql://user:password@localhost/aeon_messenger")
    
    # Telegram settings
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "test_token")
    telegram_webhook_secret: Optional[str] = os.getenv("TELEGRAM_WEBHOOK_SECRET")
    
    # JWT settings
    secret_key: str = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    
    # Redis settings
    redis_url: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # File upload settings
    upload_dir: str = os.getenv("UPLOAD_DIR", "uploads")
    max_file_size: int = int(os.getenv("MAX_FILE_SIZE", "52428800"))  # 50MB
    
    # CORS settings
    cors_origins: List[str] = []
    
    # App settings
    app_name: str = "Aeon Messenger"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Heroku settings
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Обрабатываем CORS_ORIGINS отдельно
        cors_env = os.getenv("CORS_ORIGINS", "*")
        if cors_env == "*":
            self.cors_origins = ["*"]
        else:
            self.cors_origins = [origin.strip() for origin in cors_env.split(",")]
    
    class Config:
        env_file = ".env"


settings = Settings()

# Исправляем URL базы данных для Heroku (postgres:// -> postgresql://)
if settings.database_url.startswith("postgres://"):
    settings.database_url = settings.database_url.replace("postgres://", "postgresql://", 1) 