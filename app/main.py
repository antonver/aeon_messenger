from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
import os

from app.config import settings
from app.database import get_db, engine
from app.models import user, chat, message
from app.api import chats, messages
from app.websocket import router as websocket_router
from app.auth.dependencies import get_current_user
from app.models.user import User

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
    allow_origins=settings.cors_origins,
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
app.include_router(websocket_router.router)


@app.on_event("startup")
async def startup_event():
    """Создаем таблицы при запуске приложения"""
    user.Base.metadata.create_all(bind=engine)
    chat.Base.metadata.create_all(bind=engine)
    message.Base.metadata.create_all(bind=engine)


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
        db.execute("SELECT 1")
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy",
        "database": db_status,
        "version": "1.0.0"
    }


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    Обработчик HTTP исключений
    """
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