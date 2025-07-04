import hashlib
import hmac
import json
import time
from urllib.parse import unquote_plus
from typing import Optional, Dict, Any
import logging
from app.config import settings

# Настраиваем логгер
logger = logging.getLogger(__name__)

def validate_telegram_data(init_data: str) -> Optional[Dict[str, Any]]:
    """
    Валидация данных от Telegram Mini App
    """
    try:
        logger.info("Начинаю валидацию Telegram данных")
        logger.debug(f"Полученный init_data: {init_data}")
        
        # Проверяем, что токен бота установлен правильно
        if not settings.telegram_bot_token:
            logger.error("Токен Telegram бота не установлен!")
            return None
            
        # В режиме отладки разрешаем test_token
        if settings.telegram_bot_token == "test_token" and not settings.debug:
            logger.error("Токен Telegram бота использует значение по умолчанию в продакшн режиме!")
            return None
            
        # ВРЕМЕННЫЙ РЕЖИМ ОТЛАДКИ - принимаем любые данные если debug включен
        if settings.debug:
            logger.warning("🔧 РЕЖИМ ОТЛАДКИ: Упрощенная валидация данных")
            try:
                # Парсим query string
                data_dict = {}
                for item in init_data.split('&'):
                    if '=' in item:
                        key, value = item.split('=', 1)
                        data_dict[key] = unquote_plus(value)
                
                # Если есть данные пользователя - используем их
                if 'user' in data_dict:
                    user_data = json.loads(data_dict.get('user', '{}'))
                    logger.info(f"🔧 DEBUG: Принимаем данные пользователя: {user_data.get('id')}")
                    return {
                        'user': user_data,
                        'auth_date': int(data_dict.get('auth_date', int(time.time()))),
                        'query_id': data_dict.get('query_id', 'debug_query'),
                        'start_param': data_dict.get('start_param')
                    }
                else:
                    # Создаем тестовые данные для отладки
                    logger.warning("🔧 DEBUG: Создаем тестовые данные пользователя")
                    return {
                        'user': {
                            'id': 391667619,
                            'first_name': 'Debug',
                            'last_name': 'User',
                            'username': 'debug_user'
                        },
                        'auth_date': int(time.time()),
                        'query_id': 'debug_query',
                        'start_param': None
                    }
            except Exception as e:
                logger.error(f"Ошибка в режиме отладки: {e}")
                # Возвращаем базовые тестовые данные
                return {
                    'user': {
                        'id': 391667619,
                        'first_name': 'Debug',
                        'last_name': 'User',
                        'username': 'debug_user'
                    },
                    'auth_date': int(time.time()),
                    'query_id': 'debug_query',
                    'start_param': None
                }
        
        # Парсим query string
        data_dict = {}
        for item in init_data.split('&'):
            if '=' in item:
                key, value = item.split('=', 1)
                data_dict[key] = unquote_plus(value)
        
        logger.debug(f"Распарсенные данные: {data_dict}")
        
        # Извлекаем hash для проверки
        received_hash = data_dict.pop('hash', None)
        if not received_hash:
            logger.error("Отсутствует hash в данных")
            return None
        
        # Проверяем срок действия данных (не старше 24 часов)
        auth_date = int(data_dict.get('auth_date', 0))
        current_time = int(time.time())
        if current_time - auth_date > 86400:  # 24 часа
            logger.error(f"Данные слишком старые: auth_date={auth_date}, current_time={current_time}")
            return None
        
        # Создаем строку для проверки подписи
        data_check_string = '\n'.join([f"{k}={v}" for k, v in sorted(data_dict.items())])
        logger.debug(f"Строка для проверки подписи: {data_check_string}")
        
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
        
        logger.debug(f"Ожидаемый hash: {calculated_hash}")
        logger.debug(f"Полученный hash: {received_hash}")
        
        if calculated_hash != received_hash:
            logger.error("Подпись не совпадает!")
            return None
        
        # Парсим данные пользователя
        user_data = json.loads(data_dict.get('user', '{}'))
        logger.info(f"Успешная валидация для пользователя: {user_data.get('id')}")
        
        return {
            'user': user_data,
            'auth_date': auth_date,
            'query_id': data_dict.get('query_id'),
            'start_param': data_dict.get('start_param')
        }
        
    except Exception as e:
        logger.error(f"Ошибка валидации Telegram данных: {e}", exc_info=True)
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