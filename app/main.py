from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import text
import os
import logging

from app.config import settings
from app.database import get_db, engine
from app.models import user, chat, message
from app.api import chats, messages, admin, hr
from app.websocket import router as websocket_router
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.models.chat_invitation import ChatInvitation

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG if settings.debug else logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('app.log') if not settings.debug else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

app = FastAPI(
    title=settings.app_name,
    description="Backend для мессенджера Aeon - Telegram Mini App",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=getattr(settings, 'cors_origins', ["*"]),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаем директорию для медиа файлов
os.makedirs(settings.upload_dir, exist_ok=True)

# Подключаем статические файлы для медиа
app.mount("/media", StaticFiles(directory=settings.upload_dir), name="media")

# Подключаем роуты
app.include_router(chats.router, prefix="/api/v1")
app.include_router(messages.router, prefix="/api/v1")
app.include_router(admin.router, prefix="/api/v1")
app.include_router(hr.router, prefix="/api/v1")
app.include_router(websocket_router.router)


@app.on_event("startup")
async def startup_event():
    """Создаем таблицы при запуске приложения"""
    logger.info("Запуск приложения")
    logger.info(f"Режим отладки: {settings.debug}")
    logger.info(f"Токен бота установлен: {'Да' if settings.telegram_bot_token != 'test_token' else 'НЕТ - ИСПОЛЬЗУЕТСЯ ТЕСТОВЫЙ!'}")
    
    # Создаем все таблицы
    from app.database import Base
    Base.metadata.create_all(bind=engine)
    
    logger.info("Таблицы базы данных созданы")


@app.get("/")
async def root():
    """
    Главная страница API
    """
    return {
        "message": "Aeon Messenger API",
        "version": "1.0.0",
        "status": "active"
    }


@app.get("/api/v1/me")
async def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Получение информации о текущем пользователе
    """
    return {
        "id": current_user.id,
        "telegram_id": current_user.telegram_id,
        "username": current_user.username,
        "first_name": current_user.first_name,
        "last_name": current_user.last_name,
        "language_code": current_user.language_code,
        "is_premium": current_user.is_premium,
        "is_admin": current_user.is_admin,
        "profile_photo_url": current_user.profile_photo_url,
        "bio": current_user.bio,
        "created_at": current_user.created_at
    }


@app.get("/api/v1/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Проверка здоровья API и подключения к базе данных
    """
    try:
        # Проверяем подключение к базе данных
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }


@app.get("/api/v1/debug/auth")
async def debug_auth_config():
    """
    Отладочная информация о настройках авторизации
    """
    return {
        "telegram_bot_token_set": settings.telegram_bot_token != "test_token",
        "telegram_bot_token_length": len(settings.telegram_bot_token) if settings.telegram_bot_token else 0,
        "debug_mode": settings.debug,
        "cors_origins": getattr(settings, 'cors_origins', ["*"]),
        "app_name": settings.app_name
    }


@app.post("/api/v1/debug/validate-telegram-data")
async def debug_validate_telegram_data(init_data: str):
    """
    Отладочная конечная точка для валидации Telegram данных
    """
    from app.auth.telegram import validate_telegram_data
    
    logger.info(f"Отладка валидации для: {init_data[:50]}...")
    
    result = validate_telegram_data(init_data)
    
    return {
        "success": result is not None,
        "validated_data": result,
        "telegram_bot_token_set": settings.telegram_bot_token != "test_token"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Обработчик HTTP исключений
    """
    logger.error(f"HTTP Exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    Обработчик общих исключений
    """
    logger.error(f"General Exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Внутренняя ошибка сервера",
            "status_code": 500
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug
    ) 