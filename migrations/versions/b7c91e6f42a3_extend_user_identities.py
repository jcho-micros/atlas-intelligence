"""extend user identities for identity service

Revision ID: b7c91e6f42a3
Revises: 4a8cd1b68a01
Create Date: 2026-07-17
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "b7c91e6f42a3"
down_revision: str | Sequence[str] | None = "4a8cd1b68a01"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("user_identities") as batch_op:
        batch_op.alter_column("email", existing_type=sa.String(length=255), nullable=True)
        batch_op.add_column(sa.Column("system_name", sa.String(length=160), nullable=True))
        batch_op.add_column(sa.Column("department", sa.String(length=80), nullable=True))
        batch_op.add_column(sa.Column("manager_id", sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))
        batch_op.create_index("ix_user_identities_system_name", ["system_name"], unique=False)
        batch_op.create_index("ix_user_identities_department", ["department"], unique=False)
        batch_op.create_foreign_key(
            "fk_user_identities_manager_id_user_identities",
            "user_identities",
            ["manager_id"],
            ["id"],
        )

    op.execute("UPDATE user_identities SET updated_at = created_at WHERE updated_at IS NULL")


def downgrade() -> None:
    with op.batch_alter_table("user_identities") as batch_op:
        batch_op.drop_constraint("fk_user_identities_manager_id_user_identities", type_="foreignkey")
        batch_op.drop_index("ix_user_identities_department")
        batch_op.drop_index("ix_user_identities_system_name")
        batch_op.drop_column("updated_at")
        batch_op.drop_column("manager_id")
        batch_op.drop_column("department")
        batch_op.drop_column("system_name")
        batch_op.alter_column("email", existing_type=sa.String(length=255), nullable=False)
