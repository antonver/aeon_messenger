from fastapi import HTTPException, Depends, Header
from sqlalchemy.orm import Session
from typing import Optional
from app.database import get_db
from app.models.user import User
from app.auth.telegram import validate_telegram_data, extract_user_info


async def get_current_user(
    x_telegram_init_data: Optional[str] = Header(None),
    db: Session = Depends(get_db)
) -> User:
    """
    Получение текущего пользователя из Telegram Mini App данных
    """
    if not x_telegram_init_data:
        raise HTTPException(status_code=401, detail="Отсутствуют данные авторизации")
    
    # Валидируем данные от Telegram
    validated_data = validate_telegram_data(x_telegram_init_data)
    if not validated_data:
        raise HTTPException(status_code=401, detail="Недействительные данные авторизации")
    
    # Извлекаем информацию о пользователе
    user_info = extract_user_info(validated_data)
    telegram_id = user_info.get('telegram_id')
    
    if not telegram_id:
        raise HTTPException(status_code=401, detail="Отсутствует ID пользователя")
    
    # Ищем пользователя в базе данных
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
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
        db.commit()
        db.refresh(user)
    else:
        # Обновляем данные существующего пользователя
        user.username = user_info.get('username') or user.username
        user.first_name = user_info.get('first_name') or user.first_name
        user.last_name = user_info.get('last_name') or user.last_name
        user.language_code = user_info.get('language_code', 'en')
        user.is_premium = user_info.get('is_premium', False)
        user.profile_photo_url = user_info.get('profile_photo_url') or user.profile_photo_url
        db.commit()
    
    return user 