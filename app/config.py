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
    
    # CORS settings - обрабатываем как простую строку
    cors_origins: List[str] = []

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        # Исправляем URL базы данных для Heroku (postgres:// -> postgresql://)
        if self.database_url.startswith("postgres://"):
            object.__setattr__(self, 'database_url', self.database_url.replace("postgres://", "postgresql://", 1))
                            
        # Безопасная обработка CORS_ORIGINS
        cors_env = os.getenv("CORS_ORIGINS", "")
        if not cors_env or cors_env.strip() == "":
            # Дефолтные значения если переменная не установлена
            origins = [
                "https://qit-antonvers-projects.vercel.app",
                "https://aeon-messenger.vercel.app",
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ]
        elif cors_env == "*":
            origins = ["*"]
        else:
            # Парсим строку, разделенную запятыми
            origins = []
            for origin in cors_env.split(","):
                cleaned_origin = origin.strip()
                if cleaned_origin and cleaned_origin != "":
                    origins.append(cleaned_origin)

            # Добавляем локальные домены для разработки если их нет
            local_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ]
            for local_origin in local_origins:
                if local_origin not in origins:
                    origins.append(local_origin)

        object.__setattr__(self, 'cors_origins', origins)

    class Config:
        env_file = ".env"
        # Отключаем автоматический парсинг для cors_origins
        fields = {
            "cors_origins": {"env": "CORS_ORIGINS", "parse_env_var": False}
        }


settings = Settings()
