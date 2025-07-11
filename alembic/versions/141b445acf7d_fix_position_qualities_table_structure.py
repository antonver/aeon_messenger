"""fix position_qualities table structure

Revision ID: 141b445acf7d
Revises: c2ff83739a94
Create Date: 2025-07-11 08:44:56.673377

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '141b445acf7d'
down_revision: Union[str, Sequence[str], None] = 'c2ff83739a94'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Проверяем, существует ли таблица position_qualities
    connection = op.get_bind()
    
    # Проверяем структуру таблицы position_qualities
    inspector = sa.inspect(connection)
    columns = inspector.get_columns('position_qualities')
    column_names = [col['name'] for col in columns]
    
    # Если таблица существует, но нет колонки id, добавляем её
    if 'position_qualities' in inspector.get_table_names():
        if 'id' not in column_names:
            # Добавляем колонку id
            op.add_column('position_qualities', sa.Column('id', sa.Integer(), nullable=False, primary_key=True))
            # Создаем индекс для id
            op.create_index(op.f('ix_position_qualities_id'), 'position_qualities', ['id'], unique=False)
    
    # Удаляем старую таблицу position_quality если она существует
    if 'position_quality' in inspector.get_table_names():
        op.drop_table('position_quality')


def downgrade() -> None:
    """Downgrade schema."""
    # Удаляем колонку id если она была добавлена
    connection = op.get_bind()
    inspector = sa.inspect(connection)
    columns = inspector.get_columns('position_qualities')
    column_names = [col['name'] for col in columns]
    
    if 'id' in column_names:
        op.drop_index(op.f('ix_position_qualities_id'), table_name='position_qualities')
        op.drop_column('position_qualities', 'id')
