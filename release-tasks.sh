#!/bin/bash
# Скрипт для выполнения миграций на Heroku

echo "Running database migrations..."
python -m alembic upgrade head

echo "Migrations completed!" 