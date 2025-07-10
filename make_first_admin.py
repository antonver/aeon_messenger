#!/usr/bin/env python3
"""
Скрипт для назначения первого пользователя администратором
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

def make_first_admin(app_name="aeon-backend-2892"):
    """Назначает первого пользователя администратором"""
    
    print(f"Назначение первого пользователя администратором для приложения: {app_name}")
    
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
        # Проверяем текущее состояние
        user_count = db.query(User).count()
        admin_count = db.query(User).filter(User.is_admin == True).count()
        
        print(f"Текущее состояние:")
        print(f"  - Всего пользователей: {user_count}")
        print(f"  - Администраторов: {admin_count}")
        
        if user_count == 0:
            print("❌ В базе нет пользователей")
            return
        
        if admin_count > 0:
            print("✅ В системе уже есть администраторы")
            return
        
        # Находим первого пользователя
        first_user = db.query(User).order_by(User.id).first()
        
        if not first_user:
            print("❌ Не удалось найти первого пользователя")
            return
        
        print(f"Назначаем пользователя {first_user.first_name} (ID: {first_user.id}) администратором")
        
        # Назначаем администратором
        first_user.is_admin = True
        db.commit()
        db.refresh(first_user)
        
        print(f"✅ Пользователь {first_user.first_name} успешно назначен администратором!")
        
        # Проверяем результат
        admin_count_after = db.query(User).filter(User.is_admin == True).count()
        print(f"Теперь в системе {admin_count_after} администраторов")
        
    except Exception as e:
        print(f"❌ Ошибка при назначении администратора: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Назначение первого пользователя администратором')
    parser.add_argument('--app', default='aeon-backend-2892', help='Имя приложения Heroku')
    
    args = parser.parse_args()
    make_first_admin(args.app) 