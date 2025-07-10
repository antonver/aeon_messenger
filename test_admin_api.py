#!/usr/bin/env python3
"""
Скрипт для тестирования admin API endpoints
"""
import requests
import json

def test_admin_api():
    """Тестирует admin API endpoints"""
    
    base_url = "https://aeon-backend-2892-d50dfbe26b14.herokuapp.com"
    
    print(f"Тестирование admin API endpoints")
    print(f"Base URL: {base_url}")
    
    # Тестируем /api/v1/admin/qualities
    try:
        response = requests.get(f"{base_url}/api/v1/admin/qualities")
        print(f"GET /api/v1/admin/qualities: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Qualities endpoint работает")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Qualities endpoint вернул {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании qualities: {e}")
    
    # Тестируем /api/v1/admin/positions
    try:
        response = requests.get(f"{base_url}/api/v1/admin/positions")
        print(f"GET /api/v1/admin/positions: {response.status_code}")
        if response.status_code == 200:
            print(f"✅ Positions endpoint работает")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Positions endpoint вернул {response.status_code}")
            print(f"Response: {response.text}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании positions: {e}")

if __name__ == "__main__":
    test_admin_api() 