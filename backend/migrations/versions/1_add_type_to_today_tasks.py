"""
add type column to today_tasks
"""
from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('today_tasks', sa.Column('type', sa.String(), server_default='bg-primary'))

def downgrade():
    op.drop_column('today_tasks', 'type') 