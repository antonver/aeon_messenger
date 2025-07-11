"""initial migration

Revision ID: 2ac68360ab73
Revises: 
Create Date: 2024-03-21 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone

# revision identifiers, used by Alembic.
revision = '2ac68360ab73'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'sessions',
        sa.Column('token', sa.String(), nullable=False),
        sa.Column('answers', sa.Text(), nullable=True, default='[]'),
        sa.Column('aeon_answers', sa.Text(), nullable=True, default='{}'),
        sa.Column('asked_questions', sa.Text(), nullable=True, default='[]'),
        sa.Column('current_question_index', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=lambda: datetime.now(timezone.utc)),
        sa.Column('completed', sa.Boolean(), nullable=True, default=False),
        sa.Column('question_order', sa.Text(), nullable=True, default='[]'),
        sa.Column('last_activity', sa.DateTime(), nullable=True, default=lambda: datetime.now(timezone.utc)),
        sa.PrimaryKeyConstraint('token')
    )

def downgrade():
    op.drop_table('sessions') 