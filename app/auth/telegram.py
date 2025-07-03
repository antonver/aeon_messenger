import hashlib
import hmac
import json
from urllib.parse import unquote_plus
from typing import Optional, Dict, Any
from app.config import settings


def validate_telegram_data(init_data: str) -> Optional[Dict[str, Any]]:
    """
    Валидация данных от Telegram Mini App
    """
    try:
        # Парсим query string
        data_dict = {}
        for item in init_data.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                data_dict[key] = unquote_plus(value)
        
        # Извлекаем hash для проверки
        received_hash = data_dict.pop('hash', None)
        if not received_hash:
            return None
        
        # Создаем строку для проверки подписи
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data_dict.items())])
        
        # Создаем секретный ключ
        secret_key = hmac.new(
            "WebAppData".encode(),
            settings.telegram_bot_token.encode(),
            hashlib.sha256
        ).digest()
        
        # Проверяем подпись
        calculated_hash = hmac.new(
            secret_key,
            data_check_string.encode(),
            hashlib.sha256
        ).hexdigest()
        
        if calculated_hash != received_hash:
            return None
        
        # Парсим данные пользователя
        user_data = json.loads(data_dict.get('user', '{}'))
        
        return {
            'user': user_data,
            'auth_date': int(data_dict.get('auth_date', 0)),
            'query_id': data_dict.get('query_id'),
            'start_param': data_dict.get('start_param')
        }
        
    except Exception as e:
        print(f"Ошибка валидации Telegram данных: {e}")
        return None


def extract_user_info(validated_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Извлекает информацию о пользователе из валидированных данных
    """
    user_data = validated_data.get('user', {})
    
    return {
        'telegram_id': user_data.get('id'),
        'username': user_data.get('username'),
        'first_name': user_data.get('first_name', ''),
        'last_name': user_data.get('last_name'),
        'language_code': user_data.get('language_code', 'en'),
        'is_premium': user_data.get('is_premium', False),
        'profile_photo_url': user_data.get('photo_url')
    } 