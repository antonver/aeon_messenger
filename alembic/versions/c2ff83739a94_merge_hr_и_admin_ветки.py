"""merge hr и admin ветки

Revision ID: c2ff83739a94
Revises: a569a0b9ec9f, add_hr_system_models
Create Date: 2025-07-10 19:38:44.555601

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2ff83739a94'
down_revision: Union[str, Sequence[str], None] = ('a569a0b9ec9f', 'add_hr_system_models')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
