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
    
    # App settings
    app_name: str = "Aeon Messenger"
    debug: bool = os.getenv("DEBUG", "False").lower() == "true"
    
    # Heroku settings
    port: int = int(os.getenv("PORT", "8000"))
    host: str = os.getenv("HOST", "0.0.0.0")
    
    # CORS settings
    cors_origins: List[str] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Исправляем URL базы данных для Heroku (postgres:// -> postgresql://)
        if self.database_url.startswith("postgres://"):
            object.__setattr__(self, 'database_url', self.database_url.replace("postgres://", "postgresql://", 1))

        # Обрабатываем CORS_ORIGINS
        cors_env = os.getenv("CORS_ORIGINS", "https://qit-antonvers-projects.vercel.app,https://aeon-messenger.vercel.app")
        if cors_env == "*":
            object.__setattr__(self, 'cors_origins', ["*"])
        else:
            origins = [origin.strip() for origin in cors_env.split(",") if origin.strip()]
            # Добавляем локальные домены для разработки
            origins.extend([
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
    ])
            object.__setattr__(self, 'cors_origins', origins)

    class Config:
        env_file = ".env"


settings = Settings()
