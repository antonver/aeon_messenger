import pytest
import json
import asyncio
from unittest.mock import AsyncMock, patch

from app.websocket.manager import ConnectionManager, manager
from app.models.user import User


class TestConnectionManager:
    """Тесты для менеджера WebSocket соединений"""
    
    @pytest.fixture
    def connection_manager(self):
        """Создаем новый менеджер для каждого теста"""
        return ConnectionManager()
    
    @pytest.fixture
    def mock_websocket(self):
        """Создаем мок WebSocket соединения"""
        websocket = AsyncMock()
        websocket.accept = AsyncMock()
        websocket.send_text = AsyncMock()
        return websocket
    
    @pytest.fixture
    def sample_user(self, create_user, db):
        """Создаем тестового пользователя"""
        return create_user()
    
    @pytest.mark.asyncio
    async def test_connect_user(self, connection_manager, mock_websocket, sample_user):
        """Тест подключения пользователя"""
        await connection_manager.connect(mock_websocket, sample_user)
        
        # Проверяем, что WebSocket принят
        mock_websocket.accept.assert_called_once()
        
        # Проверяем, что пользователь добавлен в активные соединения
        assert sample_user.id in connection_manager.active_connections
        assert mock_websocket in connection_manager.active_connections[sample_user.id]
        
        # Проверяем, что отправлено подтверждение подключения
        mock_websocket.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data['type'] == 'connection_established'
        assert sent_data['user_id'] == sample_user.id
    
    def test_disconnect_user(self, connection_manager, mock_websocket, sample_user):
        """Тест отключения пользователя"""
        # Сначала подключаем пользователя
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        connection_manager.user_chats[sample_user.id] = {1, 2, 3}
        connection_manager.chat_users[1] = {sample_user.id}
        connection_manager.chat_users[2] = {sample_user.id}
        connection_manager.chat_users[3] = {sample_user.id}
        
        # Отключаем пользователя
        connection_manager.disconnect(mock_websocket, sample_user.id)
        
        # Проверяем, что пользователь удален из активных соединений
        assert sample_user.id not in connection_manager.active_connections
        
        # Проверяем, что пользователь удален из всех чатов
        assert sample_user.id not in connection_manager.user_chats
        assert 1 not in connection_manager.chat_users
        assert 2 not in connection_manager.chat_users
        assert 3 not in connection_manager.chat_users
    
    @pytest.mark.asyncio
    async def test_send_personal_message(self, connection_manager, mock_websocket, sample_user):
        """Тест отправки личного сообщения"""
        # Подключаем пользователя
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        
        message = {
            'type': 'test_message',
            'content': 'Hello, user!'
        }
        
        await connection_manager.send_personal_message(message, sample_user.id)
        
        # Проверяем, что сообщение отправлено
        mock_websocket.send_text.assert_called_once()
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data['type'] == 'test_message'
        assert sent_data['content'] == 'Hello, user!'
    
    @pytest.mark.asyncio
    async def test_send_personal_message_user_offline(self, connection_manager, sample_user):
        """Тест отправки сообщения офлайн пользователю"""
        message = {
            'type': 'test_message',
            'content': 'Hello, offline user!'
        }
        
        # Пользователь не подключен
        await connection_manager.send_personal_message(message, sample_user.id)
        
        # Ничего не должно произойти (нет исключений)
        assert sample_user.id not in connection_manager.active_connections
    
    def test_join_chat(self, connection_manager, sample_user):
        """Тест добавления пользователя в чат"""
        chat_id = 123
        
        connection_manager.join_chat(sample_user.id, chat_id)
        
        # Проверяем, что пользователь добавлен в чат
        assert chat_id in connection_manager.chat_users
        assert sample_user.id in connection_manager.chat_users[chat_id]
        
        # Проверяем, что чат добавлен к пользователю
        assert sample_user.id in connection_manager.user_chats
        assert chat_id in connection_manager.user_chats[sample_user.id]
    
    def test_leave_chat(self, connection_manager, sample_user):
        """Тест удаления пользователя из чата"""
        chat_id = 123
        
        # Сначала добавляем пользователя в чат
        connection_manager.join_chat(sample_user.id, chat_id)
        
        # Затем удаляем
        connection_manager.leave_chat(sample_user.id, chat_id)
        
        # Проверяем, что пользователь удален из чата
        assert chat_id not in connection_manager.chat_users
        
        # Проверяем, что чат удален у пользователя
        assert sample_user.id not in connection_manager.user_chats
    
    @pytest.mark.asyncio
    async def test_send_to_chat(self, connection_manager, mock_websocket, sample_user, create_user, db):
        """Тест отправки сообщения в чат"""
        # Создаем второго пользователя
        user2 = create_user(telegram_id=987654321)
        mock_websocket2 = AsyncMock()
        
        chat_id = 123
        
        # Подключаем пользователей
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        connection_manager.active_connections[user2.id] = [mock_websocket2]
        
        # Добавляем пользователей в чат
        connection_manager.join_chat(sample_user.id, chat_id)
        connection_manager.join_chat(user2.id, chat_id)
        
        message = {
            'type': 'chat_message',
            'content': 'Hello, chat!'
        }
        
        await connection_manager.send_to_chat(message, chat_id)
        
        # Проверяем, что сообщение отправлено обоим пользователям
        mock_websocket.send_text.assert_called_once()
        mock_websocket2.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_to_chat_exclude_user(self, connection_manager, mock_websocket, sample_user, create_user, db):
        """Тест отправки сообщения в чат с исключением пользователя"""
        # Создаем второго пользователя
        user2 = create_user(telegram_id=987654321)
        mock_websocket2 = AsyncMock()
        
        chat_id = 123
        
        # Подключаем пользователей
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        connection_manager.active_connections[user2.id] = [mock_websocket2]
        
        # Добавляем пользователей в чат
        connection_manager.join_chat(sample_user.id, chat_id)
        connection_manager.join_chat(user2.id, chat_id)
        
        message = {
            'type': 'chat_message',
            'content': 'Hello, chat!'
        }
        
        # Отправляем сообщение, исключая первого пользователя
        await connection_manager.send_to_chat(message, chat_id, exclude_user_id=sample_user.id)
        
        # Проверяем, что сообщение отправлено только второму пользователю
        mock_websocket.send_text.assert_not_called()
        mock_websocket2.send_text.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_broadcast_typing(self, connection_manager, mock_websocket, sample_user, create_user, db):
        """Тест уведомления о печати"""
        # Создаем второго пользователя
        user2 = create_user(telegram_id=987654321)
        mock_websocket2 = AsyncMock()
        
        chat_id = 123
        
        # Подключаем пользователей
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        connection_manager.active_connections[user2.id] = [mock_websocket2]
        
        # Добавляем пользователей в чат
        connection_manager.join_chat(sample_user.id, chat_id)
        connection_manager.join_chat(user2.id, chat_id)
        
        await connection_manager.broadcast_typing(chat_id, sample_user.id, True)
        
        # Проверяем, что уведомление отправлено только второму пользователю
        mock_websocket.send_text.assert_not_called()
        mock_websocket2.send_text.assert_called_once()
        
        sent_data = json.loads(mock_websocket2.send_text.call_args[0][0])
        assert sent_data['type'] == 'typing'
        assert sent_data['chat_id'] == chat_id
        assert sent_data['user_id'] == sample_user.id
        assert sent_data['is_typing'] is True
    
    @pytest.mark.asyncio
    async def test_broadcast_message(self, connection_manager, mock_websocket, sample_user, create_user, db):
        """Тест рассылки нового сообщения"""
        # Создаем второго пользователя
        user2 = create_user(telegram_id=987654321)
        mock_websocket2 = AsyncMock()
        
        chat_id = 123
        
        # Подключаем пользователей
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        connection_manager.active_connections[user2.id] = [mock_websocket2]
        
        # Добавляем пользователей в чат
        connection_manager.join_chat(sample_user.id, chat_id)
        connection_manager.join_chat(user2.id, chat_id)
        
        message_data = {
            'id': 1,
            'text': 'New message',
            'sender_id': sample_user.id
        }
        
        await connection_manager.broadcast_message(message_data, chat_id)
        
        # Проверяем, что уведомление отправлено обоим пользователям
        mock_websocket.send_text.assert_called_once()
        mock_websocket2.send_text.assert_called_once()
        
        sent_data = json.loads(mock_websocket.send_text.call_args[0][0])
        assert sent_data['type'] == 'new_message'
        assert sent_data['chat_id'] == chat_id
        assert sent_data['message']['id'] == 1
    
    @pytest.mark.asyncio
    async def test_broadcast_message_read(self, connection_manager, mock_websocket, sample_user, create_user, db):
        """Тест уведомления о прочтении сообщения"""
        # Создаем второго пользователя
        user2 = create_user(telegram_id=987654321)
        mock_websocket2 = AsyncMock()
        
        chat_id = 123
        message_id = 456
        
        # Подключаем пользователей
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        connection_manager.active_connections[user2.id] = [mock_websocket2]
        
        # Добавляем пользователей в чат
        connection_manager.join_chat(sample_user.id, chat_id)
        connection_manager.join_chat(user2.id, chat_id)
        
        await connection_manager.broadcast_message_read(message_id, chat_id, sample_user.id)
        
        # Проверяем, что уведомление отправлено только второму пользователю
        mock_websocket.send_text.assert_not_called()
        mock_websocket2.send_text.assert_called_once()
        
        sent_data = json.loads(mock_websocket2.send_text.call_args[0][0])
        assert sent_data['type'] == 'message_read'
        assert sent_data['message_id'] == message_id
        assert sent_data['chat_id'] == chat_id
        assert sent_data['user_id'] == sample_user.id
    
    @pytest.mark.asyncio
    async def test_broadcast_user_online(self, connection_manager, mock_websocket, sample_user, create_user, db):
        """Тест уведомления об изменении статуса пользователя"""
        # Создаем второго пользователя
        user2 = create_user(telegram_id=987654321)
        mock_websocket2 = AsyncMock()
        
        chat_id = 123
        
        # Подключаем пользователей
        connection_manager.active_connections[sample_user.id] = [mock_websocket]
        connection_manager.active_connections[user2.id] = [mock_websocket2]
        
        # Добавляем пользователей в чат
        connection_manager.join_chat(sample_user.id, chat_id)
        connection_manager.join_chat(user2.id, chat_id)
        
        await connection_manager.broadcast_user_online(sample_user.id, True)
        
        # Проверяем, что уведомление отправлено только второму пользователю
        mock_websocket.send_text.assert_not_called()
        mock_websocket2.send_text.assert_called_once()
        
        sent_data = json.loads(mock_websocket2.send_text.call_args[0][0])
        assert sent_data['type'] == 'user_status'
        assert sent_data['user_id'] == sample_user.id
        assert sent_data['is_online'] is True


class TestWebSocketRouter:
    """Тесты для WebSocket роутера"""
    
    def test_websocket_endpoint_without_auth(self, client):
        """Тест WebSocket соединения без авторизации"""
        from starlette.websockets import WebSocketDisconnect
        
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws") as websocket:
                pass  # Соединение должно быть закрыто
    
    def test_websocket_endpoint_with_invalid_auth(self, client):
        """Тест WebSocket соединения с недействительной авторизацией"""
        from starlette.websockets import WebSocketDisconnect
        
        with pytest.raises(WebSocketDisconnect):
            with client.websocket_connect("/ws?init_data=invalid_data") as websocket:
                pass  # Соединение должно быть закрыто


# Интеграционные тесты с реальным WebSocket будут требовать более сложной настройки
# и использования pytest-asyncio с реальными WebSocket соединениями 