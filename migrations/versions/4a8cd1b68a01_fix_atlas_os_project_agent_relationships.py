"""fix atlas os project agent relationships

Revision ID: 4a8cd1b68a01
Revises: 27de522ee8c6
Create Date: 2026-07-06 08:57:36.391892

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4a8cd1b68a01'
down_revision: Union[str, Sequence[str], None] = '27de522ee8c6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
