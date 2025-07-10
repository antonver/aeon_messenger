#!/usr/bin/env python3
"""
Скрипт для создания таблиц в базе данных Heroku
"""
import sys
import os
import subprocess
import json
import psycopg2

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

def create_tables(app_name="aeon-backend-2892"):
    """Создает все необходимые таблицы в базе данных"""
    
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
    
    print("Создаю таблицы в базе данных...")
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()
        
        # Читаем SQL-скрипт
        with open('create_tables.sql', 'r') as f:
            sql_script = f.read()
        
        # Выполняем SQL-скрипт
        cursor.execute(sql_script)
        conn.commit()
        
        print("✅ Все таблицы созданы успешно!")
        
        # Проверяем созданные таблицы
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%'
            ORDER BY tablename
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Созданные таблицы: {', '.join(tables)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при создании таблиц: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Создание таблиц в базе данных Heroku')
    parser.add_argument('--app', default='aeon-backend-2892', help='Имя приложения Heroku')
    
    args = parser.parse_args()
    create_tables(args.app) 