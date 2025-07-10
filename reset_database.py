#!/usr/bin/env python3
"""
Скрипт для полного сброса базы данных Heroku
"""
import sys
import os
import subprocess
import json
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

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

def reset_database(app_name="aeon-backend-2892"):
    """Полностью сбрасывает базу данных"""
    
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
    
    print("⚠️  ВНИМАНИЕ: Это действие УДАЛИТ ВСЕ ДАННЫЕ из базы!")
    confirm = input("Вы уверены, что хотите полностью сбросить базу данных? (yes/no): ")
    if confirm.lower() != 'yes':
        print("Операция отменена.")
        return
    
    print("Начинаю сброс базы данных...")
    
    try:
        # Подключаемся к базе данных
        conn = psycopg2.connect(database_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Получаем список всех таблиц
        cursor.execute("""
            SELECT tablename FROM pg_tables 
            WHERE schemaname = 'public' 
            AND tablename NOT LIKE 'pg_%' 
            AND tablename != 'alembic_version'
        """)
        
        tables = [row[0] for row in cursor.fetchall()]
        print(f"Найдено таблиц для удаления: {len(tables)}")
        
        if tables:
            print("Удаляемые таблицы:", ", ".join(tables))
            
            # Удаляем все таблицы
            for table in tables:
                print(f"Удаляю таблицу: {table}")
                cursor.execute(f"DROP TABLE IF EXISTS {table} CASCADE")
            
            print("✅ Все таблицы удалены")
        else:
            print("Таблиц для удаления не найдено")
        
        cursor.close()
        conn.close()
        
        # Применяем миграции заново
        print("\nПрименяю миграции...")
        os.environ['DATABASE_URL'] = database_url
        result = subprocess.run(['alembic', 'upgrade', 'head'], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Миграции применены успешно")
        else:
            print(f"❌ Ошибка при применении миграций: {result.stderr}")
        
        print("\n🎉 База данных успешно сброшена и переинициализирована!")
        
    except Exception as e:
        print(f"❌ Ошибка при сбросе базы данных: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Полный сброс базы данных Heroku')
    parser.add_argument('--app', default='aeon-backend-2892', help='Имя приложения Heroku')
    
    args = parser.parse_args()
    reset_database(args.app) 