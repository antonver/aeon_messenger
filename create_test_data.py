#!/usr/bin/env python3
"""
Скрипт для создания тестовых данных для HR системы
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal, engine
from app.models import Position, Quality, PositionQuality, User
from sqlalchemy.orm import sessionmaker

def create_test_data():
    """Создает тестовые позиции и качества"""
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # Создаем качества
        qualities_data = [
            {"name": "Коммуникабельность"},
            {"name": "Аналитическое мышление"},
            {"name": "Командная работа"},
            {"name": "Проактивность"},
            {"name": "Технические навыки"},
            {"name": "Креативность"},
            {"name": "Организационные навыки"},
            {"name": "Стрессоустойчивость"},
            {"name": "Обучаемость"},
            {"name": "Лидерство"}
        ]
        
        qualities = []
        for quality_data in qualities_data:
            quality = Quality(**quality_data)
            db.add(quality)
            qualities.append(quality)
        
        db.commit()
        print(f"Создано {len(qualities)} качеств")
        
        # Создаем позиции
        positions_data = [
            {
                "title": "Frontend Developer",
                "is_active": True,
                "qualities": [0, 1, 2, 4, 8]  # Индексы качеств
            },
            {
                "title": "Backend Developer", 
                "is_active": True,
                "qualities": [1, 4, 5, 8, 9]
            },
            {
                "title": "Full Stack Developer",
                "is_active": True,
                "qualities": [0, 1, 2, 4, 5, 8]
            },
            {
                "title": "UI/UX Designer",
                "is_active": True,
                "qualities": [0, 2, 5, 6, 7]
            },
            {
                "title": "Product Manager",
                "is_active": True,
                "qualities": [0, 1, 2, 6, 7, 9]
            }
        ]
        
        positions = []
        for pos_data in positions_data:
            position = Position(
                title=pos_data["title"],
                is_active=pos_data["is_active"]
            )
            db.add(position)
            db.flush()  # Получаем ID позиции
            
            # Добавляем связи с качествами
            for quality_idx in pos_data["qualities"]:
                position_quality = PositionQuality(
                    position_id=position.id,
                    quality_id=qualities[quality_idx].id
                )
                db.add(position_quality)
            
            positions.append(position)
        
        db.commit()
        print(f"Создано {len(positions)} позиций")
        
        # Создаем тестового пользователя-администратора
        admin_user = User(
            telegram_id=123456789,
            first_name="Test",
            last_name="Admin",
            username="testadmin",
            is_admin=True
        )
        db.add(admin_user)
        db.commit()
        print("Создан тестовый администратор")
        
        print("✅ Тестовые данные успешно созданы!")
        
    except Exception as e:
        db.rollback()
        print(f"❌ Ошибка при создании тестовых данных: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    create_test_data() 