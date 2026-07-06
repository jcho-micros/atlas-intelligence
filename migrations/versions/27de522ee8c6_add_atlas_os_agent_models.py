"""add atlas os agent models

Revision ID: 27de522ee8c6
Revises: 947a3c89b6c4
Create Date: 2026-07-02 14:50:33.539100

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '27de522ee8c6'
down_revision: Union[str, Sequence[str], None] = '947a3c89b6c4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
