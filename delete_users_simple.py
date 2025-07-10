#!/usr/bin/env python3
"""
Простой скрипт для удаления всех пользователей из базы данных Heroku
"""
import os
import subprocess
import json
import psycopg2
from psycopg2.extras import RealDictCursor

def get_heroku_config(app_name):
    """Получает конфигурацию из Heroku"""
    try:
        result = subprocess.run(
            ['heroku', 'config', '--json', '--app', app_name],
            capture_output=True,
            text=True,
            check=True
        )
        return json.loads(result.stdout)
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при получении конфигурации Heroku: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Ошибка при парсинге JSON: {e}")
        return None

def delete_all_users_simple(app_name="aeon-backend-2892"):
    """Удаляет всех пользователей из базы данных Heroku"""
    
    print(f"Подключение к приложению Heroku: {app_name}")
    
    # Получаем конфигурацию из Heroku
    config = get_heroku_config(app_name)
    if not config:
        print("Не удалось получить конфигурацию Heroku")
        return
    
    database_url = config.get('DATABASE_URL')
    if not database_url:
        print("DATABASE_URL не найден в конфигурации")
        return
    
    print("Подключение к базе данных...")
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Проверяем количество пользователей
        cursor.execute("SELECT COUNT(*) as user_count FROM users")
        result = cursor.fetchone()
        user_count = result['user_count']
        
        print(f"Найдено пользователей в базе: {user_count}")
        
        if user_count == 0:
            print("Пользователей для удаления не найдено.")
            return
        
        # Подтверждение удаления
        print("\n⚠️  ВНИМАНИЕ: Это действие удалит ВСЕХ пользователей!")
        confirm = input(f"Вы уверены, что хотите удалить всех {user_count} пользователей? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Операция отменена.")
            return
        
        print("Начинаю удаление...")
        
        # Удаляем всех пользователей
        cursor.execute("DELETE FROM users")
        deleted_count = cursor.rowcount
        
        # Коммитим изменения
        conn.commit()
        
        print(f"✅ Успешно удалено {deleted_count} пользователей.")
        
        # Проверяем результат
        cursor.execute("SELECT COUNT(*) as remaining_users FROM users")
        result = cursor.fetchone()
        remaining_users = result['remaining_users']
        
        print(f"Осталось пользователей в базе: {remaining_users}")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователей: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Удаление всех пользователей из базы данных')
    parser.add_argument('--app', default='aeon-backend-2892', help='Имя приложения Heroku')
    
    args = parser.parse_args()
    
    print(f"Используется база данных Heroku: {args.app}")
    delete_all_users_simple(args.app) 