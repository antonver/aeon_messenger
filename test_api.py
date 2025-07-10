#!/usr/bin/env python3
"""
Скрипт для тестирования API endpoints
"""
import sys
import os
import subprocess
import json
import requests

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

def test_api_endpoints(app_name="aeon-backend-2892"):
    """Тестирует API endpoints"""
    
    print(f"Тестирование API для приложения: {app_name}")
    
    # Получаем конфигурацию из Heroku
    config = get_heroku_config(app_name)
    if not config:
        print("Не удалось получить конфигурацию Heroku")
        return
    
    base_url = f"https://{app_name}-d50dfbe26b14.herokuapp.com"
    
    print(f"Base URL: {base_url}")
    
    # Тестируем health endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/health")
        print(f"Health endpoint: {response.status_code}")
        if response.status_code == 200:
            print("✅ Health endpoint работает")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Health endpoint вернул {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании health endpoint: {e}")
    
    # Тестируем root endpoint
    try:
        response = requests.get(f"{base_url}/")
        print(f"Root endpoint: {response.status_code}")
        if response.status_code == 200:
            print("✅ Root endpoint работает")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Root endpoint вернул {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании root endpoint: {e}")
    
    # Тестируем admin-status endpoint
    try:
        response = requests.get(f"{base_url}/api/v1/users/admin-status")
        print(f"Admin status endpoint: {response.status_code}")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Admin status: {data}")
        else:
            print(f"❌ Admin status endpoint вернул {response.status_code}")
    except Exception as e:
        print(f"❌ Ошибка при тестировании admin status endpoint: {e}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Тестирование API endpoints')
    parser.add_argument('--app', default='aeon-backend-2892', help='Имя приложения Heroku')
    
    args = parser.parse_args()
    test_api_endpoints(args.app) 