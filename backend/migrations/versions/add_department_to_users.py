"""add department to users

Revision ID: add_department_to_users
Revises: 0a80fa0e3cb6
Create Date: 2025-06-18 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'add_department_to_users'
down_revision: Union[str, None] = '0a80fa0e3cb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    """Upgrade schema."""
    op.add_column('users', sa.Column('department', sa.String(), nullable=True))

def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('users', 'department') 