"""enforce canonical employee identity links

Revision ID: c2a47e195b10
Revises: b7c91e6f42a3
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op

revision: str = "c2a47e195b10"
down_revision: str | Sequence[str] | None = "b7c91e6f42a3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("user_identities") as batch_op:
        batch_op.create_unique_constraint("uq_identity_employee", ["employee_id"])


def downgrade() -> None:
    with op.batch_alter_table("user_identities") as batch_op:
        batch_op.drop_constraint("uq_identity_employee", type_="unique")
