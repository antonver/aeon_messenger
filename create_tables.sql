-- Создание таблиц для Aeon Messenger

-- Таблица пользователей
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    telegram_id BIGINT UNIQUE NOT NULL,
    username VARCHAR UNIQUE,
    first_name VARCHAR NOT NULL,
    last_name VARCHAR,
    language_code VARCHAR DEFAULT 'en',
    is_premium BOOLEAN DEFAULT FALSE,
    is_admin BOOLEAN DEFAULT FALSE,
    profile_photo_url VARCHAR,
    bio TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Таблица чатов
CREATE TABLE IF NOT EXISTS chats (
    id SERIAL PRIMARY KEY,
    title VARCHAR,
    chat_type VARCHAR NOT NULL,
    description TEXT,
    photo_url VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_by INTEGER REFERENCES users(id),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Промежуточная таблица для связи пользователей и чатов
CREATE TABLE IF NOT EXISTS chat_members (
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    joined_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_admin BOOLEAN DEFAULT FALSE,
    PRIMARY KEY (user_id, chat_id)
);

-- Таблица сообщений
CREATE TABLE IF NOT EXISTS messages (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    sender_id INTEGER REFERENCES users(id),
    text TEXT,
    message_type VARCHAR DEFAULT 'text',
    media_url VARCHAR,
    media_type VARCHAR,
    media_size INTEGER,
    media_duration INTEGER,
    reply_to_message_id INTEGER REFERENCES messages(id),
    forward_from_user_id INTEGER REFERENCES users(id),
    forward_from_chat_id INTEGER REFERENCES chats(id),
    is_edited BOOLEAN DEFAULT FALSE,
    is_deleted BOOLEAN DEFAULT FALSE,
    read_by JSON DEFAULT '[]',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Таблица приглашений в чаты
CREATE TABLE IF NOT EXISTS chat_invitations (
    id SERIAL PRIMARY KEY,
    chat_id INTEGER REFERENCES chats(id) ON DELETE CASCADE,
    username VARCHAR NOT NULL,
    invited_by INTEGER REFERENCES users(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    accepted_at TIMESTAMP WITH TIME ZONE
);

-- Таблица связи руководитель-подчиненный
CREATE TABLE IF NOT EXISTS subordinates (
    manager_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    subordinate_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    PRIMARY KEY (manager_id, subordinate_id)
);

-- HR система таблицы

-- Таблица должностей
CREATE TABLE IF NOT EXISTS positions (
    id SERIAL PRIMARY KEY,
    title VARCHAR NOT NULL,
    description TEXT,
    requirements TEXT,
    salary_range VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Таблица качеств
CREATE TABLE IF NOT EXISTS qualities (
    id SERIAL PRIMARY KEY,
    name VARCHAR NOT NULL,
    description TEXT,
    category VARCHAR,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Промежуточная таблица для связи должностей и качеств
CREATE TABLE IF NOT EXISTS position_qualities (
    position_id INTEGER REFERENCES positions(id) ON DELETE CASCADE,
    quality_id INTEGER REFERENCES qualities(id) ON DELETE CASCADE,
    weight INTEGER DEFAULT 1,
    PRIMARY KEY (position_id, quality_id)
);

-- Таблица интервью
CREATE TABLE IF NOT EXISTS interviews (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    position_id INTEGER REFERENCES positions(id) ON DELETE CASCADE,
    status VARCHAR(50) DEFAULT 'in_progress',
    score INTEGER,
    max_score INTEGER DEFAULT 100,
    answers JSON,
    questions JSON,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- Создание индексов
CREATE INDEX IF NOT EXISTS ix_users_telegram_id ON users(telegram_id);
CREATE INDEX IF NOT EXISTS ix_users_username ON users(username);
CREATE INDEX IF NOT EXISTS ix_chat_members_user_id ON chat_members(user_id);
CREATE INDEX IF NOT EXISTS ix_chat_members_chat_id ON chat_members(chat_id);
CREATE INDEX IF NOT EXISTS ix_messages_chat_id ON messages(chat_id);
CREATE INDEX IF NOT EXISTS ix_messages_sender_id ON messages(sender_id);
CREATE INDEX IF NOT EXISTS ix_chat_invitations_username ON chat_invitations(username);
CREATE INDEX IF NOT EXISTS ix_subordinates_manager_id ON subordinates(manager_id);
CREATE INDEX IF NOT EXISTS ix_subordinates_subordinate_id ON subordinates(subordinate_id);
CREATE INDEX IF NOT EXISTS ix_interviews_user_id ON interviews(user_id);
CREATE INDEX IF NOT EXISTS ix_interviews_position_id ON interviews(position_id); 