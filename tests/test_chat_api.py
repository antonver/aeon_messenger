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
    
    def test_create_chat_with_nonexistent_member(self, client, auth_headers):
        """Тест создания чата с несуществующим участником"""
        chat_data = {
            "title": "Test Chat",
            "chat_type": "group",
            "member_ids": [999999]  # Несуществующий пользователь
        }
        
        response = client.post("/api/v1/chats/", json=chat_data, headers=auth_headers)
        
        # Чат должен создаться, но несуществующий пользователь просто не добавится
        assert response.status_code == 200
    
    def test_get_user_chats_with_data(self, client, auth_headers, db, create_user, create_chat):
        """Тест получения списка чатов с данными"""
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
        
        response = client.get("/api/v1/chats/", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert len(data) == 1
        assert data[0]['id'] == chat.id
        assert data[0]['title'] == 'Test Chat'
        assert data[0]['unread_count'] == 0
    
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
    
    def test_get_nonexistent_chat(self, client, auth_headers):
        """Тест получения несуществующего чата"""
        response = client.get("/api/v1/chats/999999", headers=auth_headers)
        
        assert response.status_code == 403  # Сначала проверяется доступ
    
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
    
    def test_update_chat_not_admin(self, client, auth_headers, db, create_chat, create_user):
        """Тест обновления чата не администратором"""
        # Создаем другого пользователя как создателя чата
        admin_user = create_user(telegram_id=987654321)
        chat = create_chat(creator_id=admin_user.id, title="Test Chat")
        
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Добавляем текущего пользователя в чат как обычного участника
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=False
            )
        )
        db.commit()
        
        update_data = {
            "title": "New Title"
        }
        
        response = client.put(f"/api/v1/chats/{chat.id}", json=update_data, headers=auth_headers)
        
        assert response.status_code == 403
        assert "Недостаточно прав" in response.json()['error']
    
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
    
    def test_delete_chat_not_creator(self, client, auth_headers, create_chat, create_user):
        """Тест удаления чата не создателем"""
        # Создаем другого пользователя как создателя чата
        creator_user = create_user(telegram_id=987654321)
        chat = create_chat(creator_id=creator_user.id, title="Test Chat")
        
        response = client.delete(f"/api/v1/chats/{chat.id}", headers=auth_headers)
        
        assert response.status_code == 404
        assert "не найден или недостаточно прав" in response.json()['error']
    
    def test_add_member_to_chat(self, client, auth_headers, db, create_chat, create_user):
        """Тест добавления участника в чат"""
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Создаем чат
        chat = create_chat(creator_id=current_user_id, title="Test Chat")
        
        # Добавляем текущего пользователя как администратора
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=True
            )
        )
        db.commit()
        
        # Создаем пользователя для добавления
        new_user = create_user(telegram_id=987654321, username='newuser')
        
        response = client.post(f"/api/v1/chats/{chat.id}/members/{new_user.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "успешно добавлен" in response.json()['message']
        
        # Проверяем, что пользователь добавлен
        member = db.query(chat_members).filter(
            and_(
                chat_members.c.chat_id == chat.id,
                chat_members.c.user_id == new_user.id
            )
        ).first()
        
        assert member is not None
        assert member.is_admin is False
    
    def test_add_member_not_admin(self, client, auth_headers, db, create_chat, create_user):
        """Тест добавления участника не администратором"""
        # Создаем администратора чата
        admin_user = create_user(telegram_id=987654321)
        chat = create_chat(creator_id=admin_user.id, title="Test Chat")
        
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Добавляем текущего пользователя как обычного участника
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=False
            )
        )
        db.commit()
        
        # Создаем пользователя для добавления
        new_user = create_user(telegram_id=111222333, username='newuser')
        
        response = client.post(f"/api/v1/chats/{chat.id}/members/{new_user.id}", headers=auth_headers)
        
        assert response.status_code == 403
        assert "Недостаточно прав" in response.json()['error']
    
    def test_add_existing_member(self, client, auth_headers, db, create_chat, create_user):
        """Тест добавления уже существующего участника"""
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Создаем чат
        chat = create_chat(creator_id=current_user_id, title="Test Chat")
        
        # Добавляем текущего пользователя как администратора
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=True
            )
        )
        db.commit()
        
        # Создаем пользователя и сразу добавляем его в чат
        existing_user = create_user(telegram_id=987654321, username='existing')
        db.execute(
            chat_members.insert().values(
                user_id=existing_user.id,
                chat_id=chat.id,
                is_admin=False
            )
        )
        db.commit()
        
        response = client.post(f"/api/v1/chats/{chat.id}/members/{existing_user.id}", headers=auth_headers)
        
        assert response.status_code == 400
        assert "уже является участником" in response.json()['error']
    
    def test_remove_member_from_chat(self, client, auth_headers, db, create_chat, create_user):
        """Тест удаления участника из чата"""
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Создаем чат
        chat = create_chat(creator_id=current_user_id, title="Test Chat")
        
        # Добавляем текущего пользователя как администратора
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=True
            )
        )
        
        # Создаем и добавляем пользователя для удаления
        user_to_remove = create_user(telegram_id=987654321, username='toremove')
        db.execute(
            chat_members.insert().values(
                user_id=user_to_remove.id,
                chat_id=chat.id,
                is_admin=False
            )
        )
        db.commit()
        
        response = client.delete(f"/api/v1/chats/{chat.id}/members/{user_to_remove.id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "успешно удален" in response.json()['message']
        
        # Проверяем, что пользователь удален
        member = db.query(chat_members).filter(
            and_(
                chat_members.c.chat_id == chat.id,
                chat_members.c.user_id == user_to_remove.id
            )
        ).first()
        
        assert member is None
    
    def test_leave_chat(self, client, auth_headers, db, create_chat, create_user):
        """Тест выхода из чата"""
        # Создаем администратора чата
        admin_user = create_user(telegram_id=987654321)
        chat = create_chat(creator_id=admin_user.id, title="Test Chat")
        
        # Получаем текущего пользователя
        current_user_response = client.get("/api/v1/me", headers=auth_headers)
        current_user_id = current_user_response.json()['id']
        
        # Добавляем текущего пользователя в чат
        db.execute(
            chat_members.insert().values(
                user_id=current_user_id,
                chat_id=chat.id,
                is_admin=False
            )
        )
        db.commit()
        
        # Пользователь покидает чат (удаляет себя)
        response = client.delete(f"/api/v1/chats/{chat.id}/members/{current_user_id}", headers=auth_headers)
        
        assert response.status_code == 200
        assert "успешно удален" in response.json()['message'] 