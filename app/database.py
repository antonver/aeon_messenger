from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from app.config import settings
import logging

logger = logging.getLogger(__name__)

# Настройки для подключения к базе данных
engine_kwargs = {
    "pool_pre_ping": True,
    "pool_recycle": 300,
    "echo": settings.debug
}

# Специальные настройки для PostgreSQL на Heroku
if "postgresql://" in settings.database_url:
    engine_kwargs.update({
        "pool_size": 10,
        "max_overflow": 20,
        "pool_timeout": 30,
        "connect_args": {
            "sslmode": "require" if "heroku" in settings.database_url else "prefer"
        }
    })

try:
    engine = create_engine(settings.database_url, **engine_kwargs)
    # Тестируем соединение
    with engine.connect() as conn:
        conn.execute("SELECT 1")
    logger.info(f"База данных успешно подключена: {settings.database_url.split('@')[0]}@***")
except Exception as e:
    logger.error(f"Ошибка подключения к базе данных: {e}")
    # Создаем движок без дополнительных параметров в случае ошибки
    engine = create_engine(settings.database_url)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
