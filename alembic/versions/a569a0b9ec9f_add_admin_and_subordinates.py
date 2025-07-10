"""add_admin_and_subordinates

Revision ID: a569a0b9ec9f
Revises: 2ac68360ab73
Create Date: 2025-07-10 15:01:44.145394

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a569a0b9ec9f'
down_revision: Union[str, Sequence[str], None] = '2ac68360ab73'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Добавляем колонку is_admin в таблицу users
    op.add_column('users', sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='false'))
    
    # Создаем таблицу subordinates для связи руководитель-подчиненный
    op.create_table(
        'subordinates',
        sa.Column('manager_id', sa.Integer(), nullable=False),
        sa.Column('subordinate_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['manager_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['subordinate_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('manager_id', 'subordinate_id')
    )
    
    # Создаем индексы для оптимизации запросов
    op.create_index(
        'ix_subordinates_manager_id',
        'subordinates',
        ['manager_id']
    )
    op.create_index(
        'ix_subordinates_subordinate_id',
        'subordinates',
        ['subordinate_id']
    )


def downgrade() -> None:
    # Удаляем индексы
    op.drop_index('ix_subordinates_subordinate_id')
    op.drop_index('ix_subordinates_manager_id')
    
    # Удаляем таблицу subordinates
    op.drop_table('subordinates')
    
    # Удаляем колонку is_admin
    op.drop_column('users', 'is_admin')
