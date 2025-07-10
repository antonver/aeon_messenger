#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных с тестовыми данными
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import get_db, engine
from app.models import Position, Quality, User
from app.database import Base
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Инициализирует базу данных с тестовыми данными"""
    
    logger.info("Начинаем инициализацию базы данных...")
    
    # Создаем таблицы если их нет
    Base.metadata.create_all(bind=engine)
    logger.info("Таблицы созданы/проверены")
    
    # Тестовые качества
    test_qualities = [
        {"name": "Коммуникабельность", "description": "Умение эффективно общаться с командой"},
        {"name": "Лидерство", "description": "Способность вести команду к цели"},
        {"name": "Аналитическое мышление", "description": "Умение анализировать сложные задачи"},
        {"name": "Креативность", "description": "Способность находить нестандартные решения"},
        {"name": "Организованность", "description": "Умение планировать и структурировать работу"},
        {"name": "Адаптивность", "description": "Способность быстро адаптироваться к изменениям"},
        {"name": "Технические навыки", "description": "Владение необходимыми технологиями"},
        {"name": "Опыт работы", "description": "Релевантный опыт в сфере"},
        {"name": "Образование", "description": "Соответствующее образование"},
        {"name": "Языки программирования", "description": "Знание необходимых языков программирования"}
    ]
    
    # Тестовые позиции
    test_positions = [
        {
            "title": "Frontend Developer",
            "description": "Разработчик фронтенда с опытом React/Vue.js",
            "is_active": True
        },
        {
            "title": "Backend Developer",
            "description": "Разработчик бэкенда с опытом Python/Django/FastAPI",
            "is_active": True
        },
        {
            "title": "Full Stack Developer",
            "description": "Полноценный разработчик с опытом frontend и backend",
            "is_active": True
        },
        {
            "title": "DevOps Engineer",
            "description": "Инженер DevOps с опытом Docker, Kubernetes, CI/CD",
            "is_active": True
        },
        {
            "title": "Data Scientist",
            "description": "Специалист по машинному обучению и анализу данных",
            "is_active": True
        },
        {
            "title": "Product Manager",
            "description": "Менеджер продукта с опытом управления IT проектами",
            "is_active": True
        },
        {
            "title": "UI/UX Designer",
            "description": "Дизайнер интерфейсов с опытом Figma и Adobe Creative Suite",
            "is_active": True
        },
        {
            "title": "QA Engineer",
            "description": "Инженер по тестированию с опытом автоматизации",
            "is_active": True
        }
    ]
    
    db = next(get_db())
    
    try:
        # Проверяем и добавляем качества
        logger.info("Добавляем качества...")
        for quality_data in test_qualities:
            existing_quality = db.query(Quality).filter(Quality.name == quality_data["name"]).first()
            if not existing_quality:
                quality = Quality(**quality_data)
                db.add(quality)
                logger.info(f"Добавлено качество: {quality_data['name']}")
            else:
                logger.info(f"Качество уже существует: {quality_data['name']}")
        
        db.commit()
        logger.info("Качества обработаны")
        
        # Проверяем и добавляем позиции
        logger.info("Добавляем позиции...")
        for position_data in test_positions:
            existing_position = db.query(Position).filter(Position.title == position_data["title"]).first()
            if not existing_position:
                position = Position(**position_data)
                db.add(position)
                logger.info(f"Добавлена позиция: {position_data['title']}")
            else:
                logger.info(f"Позиция уже существует: {position_data['title']}")
        
        db.commit()
        logger.info("Позиции обработаны")
        
        # Выводим статистику
        total_positions = db.query(Position).count()
        total_qualities = db.query(Quality).count()
        total_users = db.query(User).count()
        
        logger.info(f"\nСтатистика базы данных:")
        logger.info(f"Всего позиций: {total_positions}")
        logger.info(f"Всего качеств: {total_qualities}")
        logger.info(f"Всего пользователей: {total_users}")
        
        # Проверяем подключение к базе данных
        try:
            db.execute("SELECT 1")
            logger.info("✅ Подключение к базе данных работает")
        except Exception as e:
            logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        
        logger.info("\n✅ Инициализация базы данных завершена успешно!")
        
    except Exception as e:
        logger.error(f"❌ Ошибка при инициализации: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def check_database_connection():
    """Проверяет подключение к базе данных"""
    try:
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        logger.info("✅ Подключение к базе данных работает")
        return True
    except Exception as e:
        logger.error(f"❌ Ошибка подключения к базе данных: {e}")
        return False

if __name__ == "__main__":
    logger.info("Запуск инициализации базы данных...")
    
    # Проверяем подключение
    if check_database_connection():
        init_database()
    else:
        logger.error("Не удалось подключиться к базе данных")
        sys.exit(1) 