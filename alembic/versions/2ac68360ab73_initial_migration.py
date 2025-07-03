"""Initial migration

Revision ID: 2ac68360ab73
Revises: 
Create Date: 2025-07-03 15:46:54.224434

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '2ac68360ab73'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Создаем таблицу пользователей
    op.create_table(
        'users',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('telegram_id', sa.BigInteger, unique=True, nullable=False, index=True),
        sa.Column('username', sa.String, unique=True, nullable=True),
        sa.Column('first_name', sa.String, nullable=False),
        sa.Column('last_name', sa.String, nullable=True),
        sa.Column('language_code', sa.String, nullable=True),
        sa.Column('is_premium', sa.Boolean, default=False),
        sa.Column('profile_photo_url', sa.String, nullable=True),
        sa.Column('bio', sa.Text, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Создаем таблицу чатов
    op.create_table(
        'chats',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('title', sa.String, nullable=True),
        sa.Column('chat_type', sa.String, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('photo_url', sa.String, nullable=True),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('created_by', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Создаем промежуточную таблицу для связи пользователей и чатов
    op.create_table(
        'chat_members',
        sa.Column('user_id', sa.Integer, sa.ForeignKey('users.id'), primary_key=True),
        sa.Column('chat_id', sa.Integer, sa.ForeignKey('chats.id'), primary_key=True),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('is_admin', sa.Boolean, default=False),
    )
    
    # Создаем таблицу сообщений
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer, primary_key=True, index=True),
        sa.Column('chat_id', sa.Integer, sa.ForeignKey('chats.id'), nullable=False),
        sa.Column('sender_id', sa.Integer, sa.ForeignKey('users.id'), nullable=False),
        sa.Column('text', sa.Text, nullable=True),
        sa.Column('message_type', sa.String, default='text'),
        sa.Column('media_url', sa.String, nullable=True),
        sa.Column('media_type', sa.String, nullable=True),
        sa.Column('media_size', sa.Integer, nullable=True),
        sa.Column('media_duration', sa.Integer, nullable=True),
        sa.Column('reply_to_message_id', sa.Integer, sa.ForeignKey('messages.id'), nullable=True),
        sa.Column('forward_from_user_id', sa.Integer, sa.ForeignKey('users.id'), nullable=True),
        sa.Column('forward_from_chat_id', sa.Integer, sa.ForeignKey('chats.id'), nullable=True),
        sa.Column('is_edited', sa.Boolean, default=False),
        sa.Column('is_deleted', sa.Boolean, default=False),
        sa.Column('read_by', postgresql.ARRAY(sa.Integer), default=[]),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    
    # Создаем индексы для оптимизации запросов
    op.create_index('idx_messages_chat_id', 'messages', ['chat_id'])
    op.create_index('idx_messages_sender_id', 'messages', ['sender_id'])
    op.create_index('idx_messages_created_at', 'messages', ['created_at'])
    op.create_index('idx_chat_members_user_id', 'chat_members', ['user_id'])
    op.create_index('idx_chat_members_chat_id', 'chat_members', ['chat_id'])


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем индексы
    op.drop_index('idx_chat_members_chat_id')
    op.drop_index('idx_chat_members_user_id')
    op.drop_index('idx_messages_created_at')
    op.drop_index('idx_messages_sender_id')
    op.drop_index('idx_messages_chat_id')
    
    # Удаляем таблицы в обратном порядке
    op.drop_table('messages')
    op.drop_table('chat_members')
    op.drop_table('chats')
    op.drop_table('users')
