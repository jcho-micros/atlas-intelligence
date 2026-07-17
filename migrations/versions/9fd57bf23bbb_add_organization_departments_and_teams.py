"""add organization departments and teams

Revision ID: 9fd57bf23bbb
Revises: c2a47e195b10
Create Date: 2026-07-17 13:26:57.516673

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9fd57bf23bbb'
down_revision: Union[str, Sequence[str], None] = 'c2a47e195b10'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "organization_departments",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_organization_departments_code",
        "organization_departments",
        ["code"],
        unique=False,
    )
    op.create_index(
        "ix_organization_departments_organization_id",
        "organization_departments",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_departments_status",
        "organization_departments",
        ["status"],
        unique=False,
    )

    op.create_table(
        "organization_teams",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("organization_id", sa.Integer(), nullable=False),
        sa.Column("department_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=160), nullable=False),
        sa.Column("code", sa.String(length=120), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=50), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["department_id"],
            ["organization_departments.id"],
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_organization_teams_code",
        "organization_teams",
        ["code"],
        unique=False,
    )
    op.create_index(
        "ix_organization_teams_department_id",
        "organization_teams",
        ["department_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_teams_organization_id",
        "organization_teams",
        ["organization_id"],
        unique=False,
    )
    op.create_index(
        "ix_organization_teams_status",
        "organization_teams",
        ["status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_organization_teams_status",
        table_name="organization_teams",
    )
    op.drop_index(
        "ix_organization_teams_organization_id",
        table_name="organization_teams",
    )
    op.drop_index(
        "ix_organization_teams_department_id",
        table_name="organization_teams",
    )
    op.drop_index(
        "ix_organization_teams_code",
        table_name="organization_teams",
    )
    op.drop_table("organization_teams")

    op.drop_index(
        "ix_organization_departments_status",
        table_name="organization_departments",
    )
    op.drop_index(
        "ix_organization_departments_organization_id",
        table_name="organization_departments",
    )
    op.drop_index(
        "ix_organization_departments_code",
        table_name="organization_departments",
    )
    op.drop_table("organization_departments")
