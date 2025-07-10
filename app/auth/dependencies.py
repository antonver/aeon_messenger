from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
import logging
from app.database import get_db
from app.models.user import User
from app.auth.telegram import validate_telegram_data, extract_user_info

# Настраиваем логгер
logger = logging.getLogger(__name__)

async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя из Telegram Mini App данных
    """
    logger.info("Попытка авторизации пользователя")
    
    if not x_telegram_init_data:
        logger.error("Отсутствует заголовок x-telegram-init-data")
        raise HTTPException(status_code=401, detail="Отсутствуют данные авторизации")
    
    logger.debug(f"Получен заголовок x-telegram-init-data: {x_telegram_init_data[:50]}...")
    
    try:
        # Валидируем данные от Telegram
        validated_data = validate_telegram_data(x_telegram_init_data)
        if not validated_data:
            logger.error("Валидация Telegram данных не прошла")
            raise HTTPException(status_code=401, detail="Недействительные данные авторизации")
        
        logger.info("Валидация Telegram данных успешна")
        
        # Извлекаем информацию о пользователе
        user_info = extract_user_info(validated_data)
        telegram_id = user_info.get('telegram_id')
        
        if not telegram_id:
            logger.error("Отсутствует telegram_id в данных пользователя")
            raise HTTPException(status_code=401, detail="Отсутствует ID пользователя")
        
        logger.info(f"Поиск пользователя с telegram_id: {telegram_id}")
        
        # Ищем пользователя в базе данных
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        
        if not user:
            logger.info(f"Создание нового пользователя с telegram_id: {telegram_id}")
            # Создаем нового пользователя
            user = User(
                telegram_id=telegram_id,
                username=user_info.get('username'),
                first_name=user_info.get('first_name'),
                last_name=user_info.get('last_name'),
                language_code=user_info.get('language_code', 'en'),
                is_premium=user_info.get('is_premium', False),
                profile_photo_url=user_info.get('profile_photo_url')
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
                logger.info(f"Новый пользователь создан успешно: {user.id}")
            except Exception as e:
                logger.error(f"Ошибка при создании пользователя: {e}")
                db.rollback()
                raise HTTPException(status_code=500, detail="Ошибка при создании пользователя")
        else:
            logger.info(f"Обновление данных существующего пользователя: {user.id}")
            # Обновляем данные существующего пользователя
            user.username = user_info.get('username') or user.username
            user.first_name = user_info.get('first_name') or user.first_name
            user.last_name = user_info.get('last_name') or user.last_name
            user.language_code = user_info.get('language_code', 'en')
            user.is_premium = user_info.get('is_premium', False)
            user.profile_photo_url = user_info.get('profile_photo_url') or user.profile_photo_url
            try:
                db.commit()
                logger.info(f"Данные пользователя обновлены успешно: {user.id}")
            except Exception as e:
                logger.error(f"Ошибка при обновлении пользователя: {e}")
                db.rollback()
        
        # Проверяем, есть ли администраторы в системе
        admin_exists = db.query(User).filter(User.is_admin == True).first()
        if not admin_exists:
            logger.info(f"В системе ещё нет администраторов. Назначаем пользователя {user.id} (telegram_id: {telegram_id}) первым администратором.")
            user.is_admin = True
            try:
                db.commit()
                db.refresh(user)
                logger.info(f"Пользователь {user.id} успешно назначен первым администратором системы")
            except Exception as e:
                logger.error(f"Ошибка при назначении администратора: {e}")
                db.rollback()
        else:
            logger.debug(f"В системе уже есть администраторы. Пользователь {user.id} остается обычным пользователем")
        
        return user
    
    except HTTPException:
        # Перепроброс HTTP исключений как есть
        raise
    except Exception as e:
        # Перехват всех других исключений и преобразование в 401
        logger.error(f"Неожиданная ошибка при авторизации: {e}", exc_info=True)
        raise HTTPException(status_code=401, detail="Ошибка авторизации") 