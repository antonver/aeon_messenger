import pytest
import asyncio
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import tempfile
import os
from unittest.mock import patch

# Импортируем модели напрямую, не через main.py
from app.database import get_db, Base
from app.config import settings
from app.models.user import User
from app.models.chat import Chat
from app.models.message import Message


# Тестовая база данных в памяти
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="session")
def event_loop():
    """Создаем event loop для всех тестов"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
def db():
    """Создаем тестовую базу данных для каждого теста"""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db):
    """Создаем тестовый клиент FastAPI"""
    # Мокаем настройки базы данных для тестов
    with patch('app.database.engine', engine), \
         patch('app.database.SessionLocal', TestingSessionLocal), \
         patch('app.config.settings.database_url', SQLALCHEMY_DATABASE_URL):
        
        # Импортируем приложение только когда нужно
        from app.main import app
        
        app.dependency_overrides[get_db] = override_get_db
        
        # Отключаем startup event для тестов
        app.router.on_startup = []
        
        with TestClient(app) as test_client:
            yield test_client
        
        app.dependency_overrides.clear()


@pytest.fixture
def temp_upload_dir():
    """Создаем временную директорию для загрузок"""
    with tempfile.TemporaryDirectory() as temp_dir:
        with patch.object(settings, 'upload_dir', temp_dir):
            yield temp_dir


@pytest.fixture
def mock_telegram_bot_token():
    """Мокаем токен Telegram бота"""
    with patch.object(settings, 'telegram_bot_token', 'test_bot_token'):
        yield 'test_bot_token'


@pytest.fixture
def sample_user_data():
    """Примерные данные пользователя"""
    return {
        'telegram_id': 123456789,
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'language_code': 'en',
        'is_premium': False
    }


@pytest.fixture
def sample_telegram_init_data():
    """Примерные данные Telegram Mini App"""
    import time
    
    return {
        'user': {
            'id': 123456789,
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en',
            'is_premium': False
        },
        'auth_date': int(time.time()),
        'query_id': 'test_query_id'
    }


@pytest.fixture
def create_user(db):
    """Фабрика для создания пользователей"""
    user_counter = 0
    
    def _create_user(**kwargs):
        nonlocal user_counter
        user_counter += 1
        
        user_data = {
            'telegram_id': 123456789 + user_counter,
            'username': f'testuser{user_counter}',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en',
            'is_premium': False
        }
        user_data.update(kwargs)
        
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    
    return _create_user


@pytest.fixture
def create_chat(db):
    """Фабрика для создания чатов"""
    def _create_chat(creator_id, **kwargs):
        chat_data = {
            'title': 'Test Chat',
            'chat_type': 'private',
            'created_by': creator_id,
            'is_active': True
        }
        chat_data.update(kwargs)
        
        chat = Chat(**chat_data)
        db.add(chat)
        db.commit()
        db.refresh(chat)
        return chat
    
    return _create_chat


@pytest.fixture
def create_message(db):
    """Фабрика для создания сообщений"""
    def _create_message(chat_id, sender_id, **kwargs):
        message_data = {
            'chat_id': chat_id,
            'sender_id': sender_id,
            'text': 'Test message',
            'message_type': 'text',
            'is_deleted': False
        }
        message_data.update(kwargs)
        
        message = Message(**message_data)
        db.add(message)
        db.commit()
        db.refresh(message)
        return message
    
    return _create_message


@pytest.fixture
def auth_headers(mock_telegram_bot_token):
    """Заголовки для аутентификации"""
    # Создаем валидные данные Telegram Mini App
    import json
    import hmac
    import hashlib
    import time
    from urllib.parse import quote_plus
    
    user_data = {
        'id': 123456789,
        'username': 'testuser',
        'first_name': 'Test',
        'last_name': 'User',
        'language_code': 'en',
        'is_premium': False
    }
    
    # Используем актуальное время
    current_time = int(time.time())
    
    data = {
        'user': json.dumps(user_data, separators=(',', ':')),
        'auth_date': str(current_time),
        'query_id': 'test_query_id'
    }
    
    # Создаем строку для подписи
    data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items())])
    
    # Создаем секретный ключ
    secret_key = hmac.new(
        "WebAppData".encode(),
        mock_telegram_bot_token.encode(),
        hashlib.sha256
    ).digest()
    
    # Создаем подпись
    signature = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256
    ).hexdigest()
    
    # Формируем init_data
    init_data_parts = []
    for k, v in data.items():
        init_data_parts.append(f"{k}={quote_plus(v)}")
    init_data_parts.append(f"hash={signature}")
    init_data = '&'.join(init_data_parts)
    
    return {'X-Telegram-Init-Data': init_data} 