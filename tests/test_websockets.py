import pytest
import json
from unittest.mock import AsyncMock

from app.websocket.manager import ConnectionManager


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