#!/usr/bin/env python3
"""
Тестовый скрипт для проверки логики назначения первого пользователя администратором
"""
import sys
import os
import subprocess
import json

# Добавляем путь к модулям приложения
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

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

def test_first_admin_logic(app_name="aeon-backend-2892"):
    """Тестирует логику назначения первого пользователя администратором"""
    
    print(f"Тестирование логики первого администратора для приложения: {app_name}")
    
    # Получаем конфигурацию из Heroku
    config = get_heroku_config(app_name)
    if not config:
        print("Не удалось получить конфигурацию Heroku")
        return
    
    # Устанавливаем переменные окружения
    for key, value in config.items():
        os.environ[key] = value
    
    print("Переменные окружения установлены")
    
    # Импортируем модули после установки переменных окружения
    from app.database import SessionLocal
    from app.models.user import User
    
    db = SessionLocal()
    try:
        # Проверяем текущее состояние базы данных
        user_count = db.query(User).count()
        admin_count = db.query(User).filter(User.is_admin == True).count()
        
        print(f"Текущее состояние базы данных:")
        print(f"  - Всего пользователей: {user_count}")
        print(f"  - Администраторов: {admin_count}")
        
        if user_count == 0:
            print("✅ База данных пуста - первый пользователь станет администратором")
        elif admin_count == 0:
            print("⚠️  В базе есть пользователи, но нет администраторов")
        else:
            print("✅ В системе уже есть администраторы")
        
        # Показываем всех пользователей
        users = db.query(User).all()
        if users:
            print("\nСписок пользователей:")
            for user in users:
                admin_status = "👑 АДМИН" if user.is_admin else "👤 Пользователь"
                print(f"  - {user.first_name} {user.last_name or ''} (ID: {user.id}, Telegram: {user.telegram_id}) - {admin_status}")
        else:
            print("\nПользователей в базе нет")
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Тестирование логики первого администратора')
    parser.add_argument('--app', default='aeon-backend-2892', help='Имя приложения Heroku')
    
    args = parser.parse_args()
    test_first_admin_logic(args.app) 