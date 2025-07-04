import pytest
import json
import hmac
import hashlib
from urllib.parse import urlencode, quote_plus
from unittest.mock import patch

from app.auth.telegram import validate_telegram_data, extract_user_info
from app.auth.dependencies import get_current_user
from app.models.user import User


class TestTelegramAuth:
    """Тесты для аутентификации Telegram Mini App"""
    
    def test_validate_telegram_data_success(self, mock_telegram_bot_token):
        """Тест успешной валидации данных Telegram"""
        import time
        
        user_data = {
            'id': 123456789,
            'username': 'testuser',
            'first_name': 'Test',
            'last_name': 'User',
            'language_code': 'en',
            'is_premium': False
        }
        
        current_time = int(time.time())
        data = {
            'user': json.dumps(user_data, separators=(',', ':')),  # Без пробелов
            'auth_date': str(current_time),
            'query_id': 'test_query_id'
        }
        
        # Создаем правильную подпись
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data.items())])
        
        secret_key = hmac.new(
            "WebAppData".encode(),
            mock_telegram_bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        signature = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        # Формируем данные как строку query
        init_data_parts = []
        for k, v in data.items():
            init_data_parts.append(f"{k}={quote_plus(v)}")
        init_data_parts.append(f"hash={signature}")
        init_data = '&'.join(init_data_parts)
        
        # Валидируем данные
        result = validate_telegram_data(init_data)
        
        assert result is not None
        assert result['user']['id'] == 123456789
        assert result['user']['username'] == 'testuser'
        assert result['auth_date'] == current_time
        assert result['query_id'] == 'test_query_id'
    
    def test_validate_telegram_data_invalid_signature(self, mock_telegram_bot_token):
        """Тест валидации с неверной подписью"""
        import time
        
        user_data = {
            'id': 123456789,
            'username': 'testuser',
            'first_name': 'Test'
        }
        
        data = {
            'user': json.dumps(user_data, separators=(',', ':')),
            'auth_date': str(int(time.time())),
            'hash': 'invalid_signature'
        }
        
        init_data = '&'.join([f"{k}={quote_plus(v)}" for k, v in data.items()])
        
        # Валидируем данные
        result = validate_telegram_data(init_data)
        
        assert result is None
    
    def test_validate_telegram_data_no_hash(self, mock_telegram_bot_token):
        """Тест валидации без подписи"""
        import time
        
        user_data = {
            'id': 123456789,
            'username': 'testuser',
            'first_name': 'Test'
        }
        
        data = {
            'user': json.dumps(user_data, separators=(',', ':')),
            'auth_date': str(int(time.time()))
        }
        
        init_data = '&'.join([f"{k}={quote_plus(v)}" for k, v in data.items()])
        
        # Валидируем данные
        result = validate_telegram_data(init_data)
        
        assert result is None
    
    def test_extract_user_info(self, sample_telegram_init_data):
        """Тест извлечения информации о пользователе"""
        user_info = extract_user_info(sample_telegram_init_data)
        
        assert user_info['telegram_id'] == 123456789
        assert user_info['username'] == 'testuser'
        assert user_info['first_name'] == 'Test'
        assert user_info['last_name'] == 'User'
        assert user_info['language_code'] == 'en'
        assert user_info['is_premium'] is False
    
    def test_extract_user_info_minimal(self):
        """Тест извлечения минимальной информации о пользователе"""
        minimal_data = {
            'user': {
                'id': 123456789,
                'first_name': 'Test'
            }
        }
        
        user_info = extract_user_info(minimal_data)
        
        assert user_info['telegram_id'] == 123456789
        assert user_info['username'] is None
        assert user_info['first_name'] == 'Test'
        assert user_info['last_name'] is None
        assert user_info['language_code'] == 'en'  # default
        assert user_info['is_premium'] is False  # default


class TestAuthDependencies:
    """Тесты для зависимостей аутентификации FastAPI"""
    
    def test_get_current_user_success(self, client, auth_headers):
        """Тест успешного получения текущего пользователя"""
        response = client.get("/api/v1/me", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['telegram_id'] == 123456789
        assert data['username'] == 'testuser'
        assert data['first_name'] == 'Test'
        assert data['last_name'] == 'User'
    
    def test_get_current_user_no_auth(self, client):
        """Тест получения пользователя без аутентификации"""
        response = client.get("/api/v1/me")
        
        assert response.status_code == 401
        assert "Отсутствуют данные авторизации" in response.json()['error']
    
    def test_get_current_user_invalid_auth(self, client):
        """Тест получения пользователя с неверной аутентификацией"""
        headers = {'X-Telegram-Init-Data': 'invalid_data'}
        response = client.get("/api/v1/me", headers=headers)
        
        assert response.status_code == 401
        assert "Недействительные данные авторизации" in response.json()['error']
    
    def test_user_creation_on_first_login(self, client, auth_headers, db):
        """Тест создания пользователя при первом входе"""
        # Убеждаемся, что пользователя нет
        user = db.query(User).filter(User.telegram_id == 123456789).first()
        assert user is None
        
        # Делаем запрос
        response = client.get("/api/v1/me", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Проверяем, что пользователь создался
        user = db.query(User).filter(User.telegram_id == 123456789).first()
        assert user is not None
        assert user.username == 'testuser'
        assert user.first_name == 'Test'
    
    def test_user_update_on_subsequent_login(self, client, auth_headers, db, create_user):
        """Тест обновления пользователя при повторном входе"""
        # Создаем пользователя с устаревшими данными
        user = create_user(
            telegram_id=123456789,
            username='oldusername',
            first_name='OldName'
        )
        
        # Делаем запрос с новыми данными
        response = client.get("/api/v1/me", headers=auth_headers)
        
        assert response.status_code == 200
        
        # Проверяем, что данные обновились
        db.refresh(user)
        assert user.username == 'testuser'
        assert user.first_name == 'Test' 