#!/usr/bin/env python3
"""
Скрипт для проверки состояния базы данных
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import Position, Quality, User
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def check_database():
    """Проверяет состояние базы данных"""
    
    logger.info("Проверяем состояние базы данных...")
    
    try:
        db = next(get_db())
        
        # Проверяем подключение
        db.execute("SELECT 1")
        logger.info("✅ Подключение к базе данных работает")
        
        # Проверяем таблицы
        try:
            positions_count = db.query(Position).count()
            logger.info(f"✅ Таблица positions: {positions_count} записей")
        except Exception as e:
            logger.error(f"❌ Ошибка таблицы positions: {e}")
        
        try:
            qualities_count = db.query(Quality).count()
            logger.info(f"✅ Таблица qualities: {qualities_count} записей")
        except Exception as e:
            logger.error(f"❌ Ошибка таблицы qualities: {e}")
        
        try:
            users_count = db.query(User).count()
            logger.info(f"✅ Таблица users: {users_count} записей")
        except Exception as e:
            logger.error(f"❌ Ошибка таблицы users: {e}")
        
        # Выводим несколько примеров данных
        if positions_count > 0:
            positions = db.query(Position).limit(3).all()
            logger.info("Примеры позиций:")
            for pos in positions:
                logger.info(f"  - {pos.title} (ID: {pos.id})")
        
        if qualities_count > 0:
            qualities = db.query(Quality).limit(3).all()
            logger.info("Примеры качеств:")
            for qual in qualities:
                logger.info(f"  - {qual.name} (ID: {qual.id})")
        
        db.close()
        logger.info("✅ Проверка завершена успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при проверке: {e}")
        return False
    
    return True

def test_database_operations():
    """Тестирует операции с базой данных"""
    
    logger.info("Тестируем операции с базой данных...")
    
    try:
        db = next(get_db())
        
        # Тест создания позиции
        test_position = Position(
            title="Test Position",
            description="Test Description",
            is_active=True
        )
        db.add(test_position)
        db.commit()
        logger.info("✅ Тест создания позиции прошел")
        
        # Тест создания качества
        test_quality = Quality(
            name="Test Quality",
            description="Test Quality Description"
        )
        db.add(test_quality)
        db.commit()
        logger.info("✅ Тест создания качества прошел")
        
        # Удаляем тестовые данные
        db.delete(test_position)
        db.delete(test_quality)
        db.commit()
        logger.info("✅ Тестовые данные удалены")
        
        db.close()
        logger.info("✅ Все тесты прошли успешно")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при тестировании: {e}")
        db.rollback()
        return False
    
    return True

if __name__ == "__main__":
    logger.info("Запуск проверки базы данных...")
    
    if check_database():
        logger.info("Проверка состояния завершена")
        
        # Спрашиваем пользователя о тестировании
        response = input("Хотите протестировать операции с базой данных? (y/n): ")
        if response.lower() == 'y':
            test_database_operations()
    else:
        logger.error("Проверка не удалась")
        sys.exit(1) 