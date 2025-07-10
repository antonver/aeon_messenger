#!/usr/bin/env python3
"""
Скрипт для удаления всех пользователей из базы данных
"""
import sys
import os

# Добавляем путь к модулям приложения
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import SessionLocal
from app.models.user import User
from sqlalchemy import text

def delete_all_users():
    """Удаляет всех пользователей из базы данных"""
    db = SessionLocal()
    try:
        # Получаем количество пользователей
        user_count = db.query(User).count()
        print(f"Найдено пользователей в базе: {user_count}")
        
        if user_count == 0:
            print("Пользователей для удаления не найдено.")
            return
        
        # Подтверждение удаления
        confirm = input(f"Вы уверены, что хотите удалить всех {user_count} пользователей? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Операция отменена.")
            return
        
        # Удаляем всех пользователей
        deleted_count = db.query(User).delete()
        db.commit()
        
        print(f"Успешно удалено {deleted_count} пользователей.")
        
    except Exception as e:
        print(f"Ошибка при удалении пользователей: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    delete_all_users() 