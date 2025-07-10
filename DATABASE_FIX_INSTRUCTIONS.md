# Инструкции по исправлению проблемы с сохранением данных

## Проблема
После закрытия приложения качества и позиции не сохраняются в базе данных.

## Возможные причины

### 1. Временная база данных на Heroku
Heroku может использовать временную базу данных, которая сбрасывается при перезапуске.

### 2. Проблемы с подключением к базе данных
Неправильная конфигурация DATABASE_URL или проблемы с подключением.

### 3. Отсутствие миграций
Таблицы не созданы или созданы неправильно.

## Решение

### Шаг 1: Проверка базы данных

Запустите скрипт проверки:
```bash
cd backend
python check_database.py
```

### Шаг 2: Инициализация базы данных

Если база данных пустая, запустите инициализацию:
```bash
cd backend
python init_database.py
```

### Шаг 3: Проверка на Heroku

Проверьте состояние базы данных на Heroku:
```bash
heroku run python check_database.py --app aeon-backend-2892-d50dfbe26b14
```

### Шаг 4: Инициализация на Heroku

Если база данных пустая на Heroku:
```bash
heroku run python init_database.py --app aeon-backend-2892-d50dfbe26b14
```

### Шаг 5: Проверка переменных окружения

Убедитесь, что DATABASE_URL настроен правильно:
```bash
heroku config:get DATABASE_URL --app aeon-backend-2892-d50dfbe26b14
```

### Шаг 6: Применение миграций

Примените миграции на Heroku:
```bash
heroku run alembic upgrade head --app aeon-backend-2892-d50dfbe26b14
```

## Улучшения в коде

### 1. Добавлено логирование
В endpoints для создания позиций и качеств добавлено подробное логирование для отслеживания ошибок.

### 2. Обработка ошибок
Добавлена обработка исключений с rollback транзакций при ошибках.

### 3. Скрипты диагностики
Созданы скрипты для проверки и инициализации базы данных.

## Проверка работоспособности

### Тест API endpoints

1. **Создание позиции:**
```bash
curl -X POST "https://aeon-backend-2892-d50dfbe26b14.herokuapp.com/api/v1/admin/positions" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Test Position",
    "description": "Test Description",
    "is_active": true
  }'
```

2. **Создание качества:**
```bash
curl -X POST "https://aeon-backend-2892-d50dfbe26b14.herokuapp.com/api/v1/admin/qualities" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Test Quality",
    "description": "Test Quality Description"
  }'
```

3. **Получение позиций:**
```bash
curl -X GET "https://aeon-backend-2892-d50dfbe26b14.herokuapp.com/api/v1/admin/positions"
```

4. **Получение качеств:**
```bash
curl -X GET "https://aeon-backend-2892-d50dfbe26b14.herokuapp.com/api/v1/admin/qualities"
```

## Логи

Проверьте логи приложения для диагностики:
```bash
heroku logs --tail --app aeon-backend-2892-d50dfbe26b14
```

## Возможные решения проблем

### Если база данных временная:
- Рассмотрите переход на платную базу данных PostgreSQL на Heroku
- Используйте внешнюю базу данных (например, AWS RDS)

### Если проблемы с подключением:
- Проверьте DATABASE_URL в переменных окружения
- Убедитесь, что база данных доступна

### Если таблицы не созданы:
- Примените миграции: `alembic upgrade head`
- Проверьте, что все модели импортированы в `app/models/__init__.py`

## Контакты

При возникновении проблем проверьте логи и обратитесь к команде разработки. 