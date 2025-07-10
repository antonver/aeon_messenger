-- Скрипт для удаления всех пользователей из базы данных
-- ВНИМАНИЕ: Этот скрипт удалит ВСЕХ пользователей!

-- Проверяем количество пользователей
SELECT COUNT(*) as user_count FROM users;

-- Удаляем всех пользователей
DELETE FROM users;

-- Проверяем результат
SELECT COUNT(*) as remaining_users FROM users; 