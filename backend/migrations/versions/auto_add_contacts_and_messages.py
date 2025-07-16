"""add contacts and messages tables

Revision ID: auto_add_contacts_and_messages
Revises: 
Create Date: 2025-06-18 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'auto_add_contacts_and_messages'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table(
        'contacts',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('contact_user_id', sa.Integer(), nullable=False)
    )
    op.create_table(
        'messages',
        sa.Column('id', sa.Integer(), primary_key=True, index=True),
        sa.Column('from_user_id', sa.Integer(), nullable=False),
        sa.Column('to_user_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('time', sa.DateTime(), nullable=False)
    )

def downgrade() -> None:
    op.drop_table('messages')
    op.drop_table('contacts') 