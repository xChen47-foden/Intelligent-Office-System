"""add participants to meetings

Revision ID: add_participants_to_meetings
Revises: 
Create Date: 2025-01-25 20:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'add_participants_to_meetings'
down_revision = None
depends_on = None

def upgrade():
    # 添加participants字段到meetings表
    op.add_column('meetings', sa.Column('participants', sa.String(), nullable=True, default=''))
    
    # 添加host_user_id字段到meetings表
    op.add_column('meetings', sa.Column('host_user_id', sa.Integer(), nullable=True, default=0))

def downgrade():
    # 删除添加的字段
    op.drop_column('meetings', 'participants')
    op.drop_column('meetings', 'host_user_id') 