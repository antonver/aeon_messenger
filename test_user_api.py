#!/usr/bin/env python3
"""
Скрипт для тестирования API пользователя
"""
import requests
import json

def test_user_api():
    """Тестирует API пользователя"""
    
    base_url = "https://aeon-backend-2892-d50dfbe26b14.herokuapp.com"
    
    print(f"Тестирование API пользователя")
    print(f"Base URL: {base_url}")
    
    # Тестируем /api/v1/me endpoint
    try:
        # Имитируем Telegram WebApp данные
        headers = {
            'x-telegram-init-data': 'user=%7B%22id%22%3A391667619%2C%22first_name%22%3A%22Anton%22%2C%22last_name%22%3A%22%22%2C%22username%22%3A%22AntonioDaVinchi%22%2C%22language_code%22%3A%22fr%22%2C%22allows_write_to_pm%22%3Atrue%2C%22photo_url%22%3A%22https%3A%5C%2F%5C%2Ft.me%5C%2Fi%5C%2Fuserpic%5C%2F320%5C%2F511EN4x-FSsb57qIhBwxIm1vBlwG8HygTsW7P-6LKkw.svg%22%7D&chat_instance=-347241825810697583&chat_type=private&auth_date=1752169597&signature=HDbdXhFBtoMtFKHXkje6TU6wR9rNessjhHXnIOKdVjajZrUol2Gi5sKBRRE8N2W4JgGbI_TBE6q5NTLPBXlbCA&hash=d3f05831b981939ffc1e1cb25b3406f3091975a8c34b1dfb5bd47e1bab4316fa'
        }
        
        response = requests.get(f"{base_url}/api/v1/me", headers=headers)
        print(f"User API endpoint: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User API работает")
            print(f"Response: {json.dumps(data, indent=2, ensure_ascii=False)}")
            
            # Проверяем поле is_admin
            if 'is_admin' in data:
                print(f"🔍 is_admin: {data['is_admin']}")
            else:
                print("❌ Поле is_admin отсутствует в ответе")
        else:
            print(f"❌ User API вернул {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании user API: {e}")

if __name__ == "__main__":
    test_user_api() 