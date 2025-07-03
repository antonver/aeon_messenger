import pytest
from sqlalchemy import and_

from app.models.chat import chat_members


class TestChatAPI:
    """Тесты для API чатов"""
    
    def test_get_user_chats_empty(self, client, auth_headers):
        """Тест получения пустого списка чатов"""
        response = client.get("/api/v1/chats/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data == []
    
    def test_create_private_chat(self, client, auth_headers, db, create_user):
        """Тест создания приватного чата"""
        # Создаем второго пользователя для приватного чата
        user2 = create_user(telegram_id=987654321, username='user2')
        
        chat_data = {
            "chat_type": "private",
            "member_ids": [user2.id]
        }
        
        response = client.post("/api/v1/chats/", json=chat_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['chat_type'] == 'private'
        assert data['title'] is None  # Приватный чат без названия
        assert data['is_active'] is True
        assert data['created_by'] is not None
    
    def test_create_group_chat(self, client, auth_headers, db, create_user):
        """Тест создания группового чата"""
        # Создаем пользователей для группы
        user2 = create_user(telegram_id=987654321, username='user2')
        user3 = create_user(telegram_id=111222333, username='user3')
        
        chat_data = {
            "title": "Test Group",
            "chat_type": "group",
            "description": "Test group description",
            "member_ids": [user2.id, user3.id]
        }
        
        response = client.post("/api/v1/chats/", json=chat_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['title'] == 'Test Group'
        assert data['chat_type'] == 'group'
        assert data['description'] == 'Test group description'
        assert data['is_active'] is True
    
    def test_get_chat_by_id(self, client, auth_headers, db, create_chat):
        """Тест получения чата по ID"""
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
        
        response = client.get(f"/api/v1/chats/{chat.id}", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['id'] == chat.id
        assert data['title'] == 'Test Chat'
        assert data['created_by'] == current_user_id
    
    def test_get_chat_access_denied(self, client, auth_headers, create_chat, create_user):
        """Тест запрета доступа к чужому чату"""
        # Создаем другого пользователя и его чат
        other_user = create_user(telegram_id=987654321)
        chat = create_chat(creator_id=other_user.id, title="Other's Chat")
        
        response = client.get(f"/api/v1/chats/{chat.id}", headers=auth_headers)
        
        assert response.status_code == 403
        assert "Доступ запрещен" in response.json()['error']
    
    def test_update_chat(self, client, auth_headers, db, create_chat):
        """Тест обновления чата"""
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Создаем чат
        chat = create_chat(creator_id=current_user_id, title="Old Title")
        
        # Добавляем пользователя в чат как администратора
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=True
            )
        )
        db.commit()
        
        update_data = {
            "title": "New Title",
            "description": "New description"
        }
        
        response = client.put(f"/api/v1/chats/{chat.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['title'] == 'New Title'
        assert data['description'] == 'New description'
    
    def test_delete_chat(self, client, auth_headers, db, create_chat):
        """Тест удаления чата"""
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Создаем чат
        chat = create_chat(creator_id=current_user_id, title="Chat to Delete")
        
        response = client.delete(f"/api/v1/chats/{chat.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "успешно удален" in response.json()['message']
        
        # Проверяем, что чат помечен как неактивный
        db.refresh(chat)
        assert chat.is_active is False 