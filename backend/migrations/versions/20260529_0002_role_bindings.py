"""add role bindings

Revision ID: 20260529_0002
Revises: 20260528_0001
Create Date: 2026-05-29
"""

from alembic import op
import sqlalchemy as sa


revision = "20260529_0002"
down_revision = "20260528_0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "role_bindings",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("display_name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("openid", sa.String(length=120), nullable=False),
        sa.Column("enabled", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_role_bindings_enabled", "role_bindings", ["enabled"])
    op.create_index("ix_role_bindings_openid", "role_bindings", ["openid"], unique=True)
    op.create_index("ix_role_bindings_role", "role_bindings", ["role"])
    op.create_index("ix_role_bindings_store_id", "role_bindings", ["store_id"])
    op.create_index("ix_role_bindings_user_id", "role_bindings", ["user_id"], unique=True)


def downgrade() -> None:
    op.drop_index("ix_role_bindings_user_id", table_name="role_bindings")
    op.drop_index("ix_role_bindings_store_id", table_name="role_bindings")
    op.drop_index("ix_role_bindings_role", table_name="role_bindings")
    op.drop_index("ix_role_bindings_openid", table_name="role_bindings")
    op.drop_index("ix_role_bindings_enabled", table_name="role_bindings")
    op.drop_table("role_bindings")
