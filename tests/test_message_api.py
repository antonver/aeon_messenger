import pytest
import io
from sqlalchemy import and_

from app.models.chat import chat_members
from app.models.message import Message


class TestMessageAPI:
    """Тесты для API сообщений"""
    
    def setup_chat_with_user(self, client, auth_headers, db, create_chat):
        """Вспомогательный метод для создания чата с пользователем"""
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Создаем чат
        chat = create_chat(creator_id=current_user_id, title="Test Chat")
        
        # Добавляем пользователя в чат
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=True
            )
        )
        db.commit()
        
        return chat, current_user_id
    
    def test_get_chat_messages_empty(self, client, auth_headers, db, create_chat):
        """Тест получения пустого списка сообщений"""
        chat, _ = self.setup_chat_with_user(client, auth_headers, db, create_chat)
        
        response = client.get(f"/api/v1/messages/chat/{chat.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['messages'] == []
        assert data['total'] == 0
        assert data['page'] == 1
        assert data['per_page'] == 50
        assert data['has_next'] is False
        assert data['has_prev'] is False
    
    def test_send_text_message(self, client, auth_headers, db, create_chat):
        """Тест отправки текстового сообщения"""
        chat, _ = self.setup_chat_with_user(client, auth_headers, db, create_chat)
        
        message_data = {
            "chat_id": chat.id,
            "text": "Hello, world!",
            "message_type": "text"
        }
        
        response = client.post("/api/v1/messages/", json=message_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['chat_id'] == chat.id
        assert data['text'] == 'Hello, world!'
        assert data['message_type'] == 'text'
        assert data['is_edited'] is False
        assert data['is_deleted'] is False
        assert data['sender'] is not None
    
    def test_edit_message(self, client, auth_headers, db, create_chat, create_message):
        """Тест редактирования сообщения"""
        chat, user_id = self.setup_chat_with_user(client, auth_headers, db, create_chat)
        
        # Создаем сообщение
        message = create_message(chat.id, user_id, text="Original text")
        
        update_data = {
            "text": "Edited text"
        }
        
        response = client.put(f"/api/v1/messages/{message.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['text'] == 'Edited text'
        assert data['is_edited'] is True
    
    def test_delete_message(self, client, auth_headers, db, create_chat, create_message):
        """Тест удаления сообщения"""
        chat, user_id = self.setup_chat_with_user(client, auth_headers, db, create_chat)
        
        # Создаем сообщение
        message = create_message(chat.id, user_id, text="Message to delete")
        
        response = client.delete(f"/api/v1/messages/{message.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "успешно удалено" in response.json()['message']
        
        # Проверяем, что сообщение помечено как удаленное
        db.refresh(message)
        assert message.is_deleted is True
        assert message.text is None
    
    def test_upload_media_file(self, client, auth_headers, temp_upload_dir):
        """Тест загрузки медиа файла"""
        # Создаем тестовый файл
        test_file_content = b"test image content"
        test_file = io.BytesIO(test_file_content)
        
        files = {
            'file': ('test_image.jpg', test_file, 'image/jpeg')
        }
        
        response = client.post("/api/v1/messages/upload-media", files=files, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['media_type'] == 'image/jpeg'
        assert data['media_size'] == len(test_file_content)
        assert data['message_type'] == 'photo'
        assert data['filename'] == 'test_image.jpg'
        assert data['media_url'].startswith('/media/') 