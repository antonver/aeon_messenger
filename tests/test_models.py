import pytest
from datetime import datetime
from sqlalchemy import and_

from app.models.user import User
from app.models.chat import Chat, chat_members
from app.models.message import Message


class TestUserModel:
    """Тесты для модели User"""
    
    def test_create_user(self, db):
        """Тест создания пользователя"""
        user = User(
            telegram_id=123456789,
            username='testuser',
            first_name='Test',
            last_name='User',
            language_code='en',
            is_premium=False
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.id is not None
        assert user.telegram_id == 123456789
        assert user.username == 'testuser'
        assert user.first_name == 'Test'
        assert user.last_name == 'User'
        assert user.language_code == 'en'
        assert user.is_premium is False
        assert user.is_active is True
        assert user.created_at is not None
        assert isinstance(user.created_at, datetime)
    
    def test_user_unique_telegram_id(self, db):
        """Тест уникальности telegram_id"""
        user1 = User(
            telegram_id=123456789,
            first_name='Test1'
        )
        user2 = User(
            telegram_id=123456789,
            first_name='Test2'
        )
        
        db.add(user1)
        db.commit()
        
        db.add(user2)
        
        with pytest.raises(Exception):  # Должна быть ошибка уникальности
            db.commit()
    
    def test_user_unique_username(self, db):
        """Тест уникальности username"""
        user1 = User(
            telegram_id=123456789,
            username='testuser',
            first_name='Test1'
        )
        user2 = User(
            telegram_id=987654321,
            username='testuser',
            first_name='Test2'
        )
        
        db.add(user1)
        db.commit()
        
        db.add(user2)
        
        with pytest.raises(Exception):  # Должна быть ошибка уникальности
            db.commit()
    
    def test_user_optional_fields(self, db):
        """Тест необязательных полей пользователя"""
        user = User(
            telegram_id=123456789,
            first_name='Test'
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        assert user.username is None
        assert user.last_name is None
        assert user.profile_photo_url is None
        assert user.bio is None
        assert user.language_code == 'en'  # default
        assert user.is_premium is False  # default
        assert user.is_active is True  # default


class TestChatModel:
    """Тесты для модели Chat"""
    
    def test_create_private_chat(self, db, create_user):
        """Тест создания приватного чата"""
        user = create_user()
        
        chat = Chat(
            chat_type='private',
            created_by=user.id
        )
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        assert chat.id is not None
        assert chat.title is None  # Приватный чат без названия
        assert chat.chat_type == 'private'
        assert chat.created_by == user.id
        assert chat.is_active is True
        assert chat.created_at is not None
        assert isinstance(chat.created_at, datetime)
    
    def test_create_group_chat(self, db, create_user):
        """Тест создания группового чата"""
        user = create_user()
        
        chat = Chat(
            title='Test Group',
            chat_type='group',
            description='Test group description',
            created_by=user.id
        )
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        assert chat.title == 'Test Group'
        assert chat.chat_type == 'group'
        assert chat.description == 'Test group description'
        assert chat.created_by == user.id
    
    def test_chat_members_relationship(self, db, create_user):
        """Тест связи чата с участниками"""
        user1 = create_user(telegram_id=123456789)
        user2 = create_user(telegram_id=987654321)
        
        chat = Chat(
            title='Test Chat',
            chat_type='group',
            created_by=user1.id
        )
        
        db.add(chat)
        db.commit()
        db.refresh(chat)
        
        # Добавляем участников
        db.execute(
            chat_members.insert().values(
                user_id=user1.id,
                chat_id=chat.id,
                is_admin=True
            )
        )
        db.execute(
            chat_members.insert().values(
                user_id=user2.id,
                chat_id=chat.id,
                is_admin=False
            )
        )
        db.commit()
        
        # Проверяем участников
        members = db.query(chat_members).filter(
            chat_members.c.chat_id == chat.id
        ).all()
        
        assert len(members) == 2
        
        # Проверяем администратора
        admin = db.query(chat_members).filter(
            and_(
                chat_members.c.chat_id == chat.id,
                chat_members.c.is_admin == True
            )
        ).first()
        
        assert admin.user_id == user1.id


class TestMessageModel:
    """Тесты для модели Message"""
    
    def test_create_text_message(self, db, create_user, create_chat):
        """Тест создания текстового сообщения"""
        user = create_user()
        chat = create_chat(creator_id=user.id)
        
        message = Message(
            chat_id=chat.id,
            sender_id=user.id,
            text='Hello, world!',
            message_type='text'
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        assert message.id is not None
        assert message.chat_id == chat.id
        assert message.sender_id == user.id
        assert message.text == 'Hello, world!'
        assert message.message_type == 'text'
        assert message.is_edited is False
        assert message.is_deleted is False
        assert message.read_by == []
        assert message.created_at is not None
        assert isinstance(message.created_at, datetime)
    
    def test_create_media_message(self, db, create_user, create_chat):
        """Тест создания медиа сообщения"""
        user = create_user()
        chat = create_chat(creator_id=user.id)
        
        message = Message(
            chat_id=chat.id,
            sender_id=user.id,
            text='Check out this photo!',
            message_type='photo',
            media_url='/media/photo.jpg',
            media_type='image/jpeg',
            media_size=1024000
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        assert message.message_type == 'photo'
        assert message.media_url == '/media/photo.jpg'
        assert message.media_type == 'image/jpeg'
        assert message.media_size == 1024000
    
    def test_create_voice_message(self, db, create_user, create_chat):
        """Тест создания голосового сообщения"""
        user = create_user()
        chat = create_chat(creator_id=user.id)
        
        message = Message(
            chat_id=chat.id,
            sender_id=user.id,
            message_type='voice',
            media_url='/media/voice.ogg',
            media_type='audio/ogg',
            media_size=512000,
            media_duration=30
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        assert message.message_type == 'voice'
        assert message.media_duration == 30
        assert message.text is None  # Голосовое сообщение без текста
    
    def test_reply_message(self, db, create_user, create_chat):
        """Тест ответа на сообщение"""
        user = create_user()
        chat = create_chat(creator_id=user.id)
        
        # Создаем исходное сообщение
        original_message = Message(
            chat_id=chat.id,
            sender_id=user.id,
            text='Original message'
        )
        
        db.add(original_message)
        db.commit()
        db.refresh(original_message)
        
        # Создаем ответ
        reply_message = Message(
            chat_id=chat.id,
            sender_id=user.id,
            text='Reply to original',
            reply_to_message_id=original_message.id
        )
        
        db.add(reply_message)
        db.commit()
        db.refresh(reply_message)
        
        assert reply_message.reply_to_message_id == original_message.id
    
    def test_forward_message(self, db, create_user, create_chat):
        """Тест пересылки сообщения"""
        user1 = create_user(telegram_id=123456789)
        user2 = create_user(telegram_id=987654321)
        chat1 = create_chat(creator_id=user1.id)
        chat2 = create_chat(creator_id=user2.id)
        
        # Создаем исходное сообщение
        original_message = Message(
            chat_id=chat1.id,
            sender_id=user1.id,
            text='Original message'
        )
        
        db.add(original_message)
        db.commit()
        db.refresh(original_message)
        
        # Создаем пересланное сообщение
        forwarded_message = Message(
            chat_id=chat2.id,
            sender_id=user2.id,
            text='Original message',
            forward_from_user_id=user1.id,
            forward_from_chat_id=chat1.id
        )
        
        db.add(forwarded_message)
        db.commit()
        db.refresh(forwarded_message)
        
        assert forwarded_message.forward_from_user_id == user1.id
        assert forwarded_message.forward_from_chat_id == chat1.id
    
    def test_message_read_status(self, db, create_user, create_chat):
        """Тест статуса прочтения сообщения"""
        user1 = create_user(telegram_id=123456789)
        user2 = create_user(telegram_id=987654321)
        chat = create_chat(creator_id=user1.id)
        
        message = Message(
            chat_id=chat.id,
            sender_id=user1.id,
            text='Test message',
            read_by=[]
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Отмечаем как прочитанное пользователем 2
        message.read_by = [user2.id]
        db.commit()
        db.refresh(message)
        
        assert user2.id in message.read_by
        assert user1.id not in message.read_by
    
    def test_message_edit(self, db, create_user, create_chat):
        """Тест редактирования сообщения"""
        user = create_user()
        chat = create_chat(creator_id=user.id)
        
        message = Message(
            chat_id=chat.id,
            sender_id=user.id,
            text='Original text',
            is_edited=False
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Редактируем сообщение
        message.text = 'Edited text'
        message.is_edited = True
        db.commit()
        db.refresh(message)
        
        assert message.text == 'Edited text'
        assert message.is_edited is True
    
    def test_message_delete(self, db, create_user, create_chat):
        """Тест удаления сообщения"""
        user = create_user()
        chat = create_chat(creator_id=user.id)
        
        message = Message(
            chat_id=chat.id,
            sender_id=user.id,
            text='Message to delete',
            is_deleted=False
        )
        
        db.add(message)
        db.commit()
        db.refresh(message)
        
        # Удаляем сообщение
        message.is_deleted = True
        message.text = None
        db.commit()
        db.refresh(message)
        
        assert message.is_deleted is True
        assert message.text is None 