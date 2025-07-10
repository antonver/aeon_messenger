#!/usr/bin/env python3
"""
Скрипт для удаления всех пользователей из базы данных Heroku
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

def delete_all_users_with_heroku(app_name="aeon-backend-2892"):
    """Удаляет всех пользователей из базы данных Heroku"""
    
    print(f"Подключение к приложению Heroku: {app_name}")
    
    # Получаем конфигурацию из Heroku
    config = get_heroku_config(app_name)
    if not config:
        print("Не удалось получить конфигурацию Heroku")
        return
    
    # Устанавливаем переменные окружения
    for key, value in config.items():
        os.environ[key] = value
    
    print("Переменные окружения установлены")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'НЕ УСТАНОВЛЕН')[:50]}...")
    
    # Теперь импортируем модули после установки переменных окружения
    from app.database import SessionLocal
    from app.models.user import User
    from app.models.chat import Chat
    from app.models.message import Message
    from app.models.chat_invitation import ChatInvitation
    from app.models.interview import Interview
    
    db = SessionLocal()
    try:
        # Получаем статистику перед удалением
        user_count = db.query(User).count()
        chat_count = db.query(Chat).count()
        message_count = db.query(Message).count()
        invitation_count = db.query(ChatInvitation).count()
        interview_count = db.query(Interview).count()
        
        print(f"Статистика базы данных:")
        print(f"  - Пользователей: {user_count}")
        print(f"  - Чатов: {chat_count}")
        print(f"  - Сообщений: {message_count}")
        print(f"  - Приглашений: {invitation_count}")
        print(f"  - Интервью: {interview_count}")
        
        if user_count == 0:
            print("Пользователей для удаления не найдено.")
            return
        
        # Подтверждение удаления
        print("\n⚠️  ВНИМАНИЕ: Это действие удалит ВСЕХ пользователей и связанные данные!")
        confirm = input(f"Вы уверены, что хотите удалить всех {user_count} пользователей? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Операция отменена.")
            return
        
        print("Начинаю удаление...")
        
        # Удаляем связанные данные в правильном порядке
        # 1. Удаляем интервью
        deleted_interviews = db.query(Interview).delete()
        print(f"Удалено интервью: {deleted_interviews}")
        
        # 2. Удаляем приглашения в чаты
        deleted_invitations = db.query(ChatInvitation).delete()
        print(f"Удалено приглашений: {deleted_invitations}")
        
        # 3. Удаляем сообщения
        deleted_messages = db.query(Message).delete()
        print(f"Удалено сообщений: {deleted_messages}")
        
        # 4. Удаляем чаты (связи с пользователями удалятся автоматически)
        deleted_chats = db.query(Chat).delete()
        print(f"Удалено чатов: {deleted_chats}")
        
        # 5. Удаляем пользователей
        deleted_users = db.query(User).delete()
        print(f"Удалено пользователей: {deleted_users}")
        
        # Коммитим изменения
        db.commit()
        
        print(f"\n✅ Успешно удалено:")
        print(f"  - {deleted_users} пользователей")
        print(f"  - {deleted_chats} чатов")
        print(f"  - {deleted_messages} сообщений")
        print(f"  - {deleted_invitations} приглашений")
        print(f"  - {deleted_interviews} интервью")
        
        # Проверяем результат
        remaining_users = db.query(User).count()
        print(f"\nОсталось пользователей в базе: {remaining_users}")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователей: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def delete_users_local():
    """Удаляет пользователей из локальной базы данных"""
    from app.database import SessionLocal
    from app.models.user import User
    
    db = SessionLocal()
    try:
        user_count = db.query(User).count()
        print(f"Найдено пользователей в локальной базе: {user_count}")
        
        if user_count == 0:
            print("Пользователей для удаления не найдено.")
            return
        
        confirm = input(f"Вы уверены, что хотите удалить всех {user_count} пользователей из локальной базы? (yes/no): ")
        if confirm.lower() != 'yes':
            print("Операция отменена.")
            return
        
        deleted_count = db.query(User).delete()
        db.commit()
        
        print(f"✅ Успешно удалено {deleted_count} пользователей из локальной базы.")
        
    except Exception as e:
        print(f"❌ Ошибка при удалении пользователей: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Удаление всех пользователей из базы данных')
    parser.add_argument('--app', default='aeon-backend-2892', help='Имя приложения Heroku')
    parser.add_argument('--local', action='store_true', help='Использовать локальную базу данных')
    
    args = parser.parse_args()
    
    if args.local:
        print("Используется локальная база данных")
        delete_users_local()
    else:
        print(f"Используется база данных Heroku: {args.app}")
        delete_all_users_with_heroku(args.app) 