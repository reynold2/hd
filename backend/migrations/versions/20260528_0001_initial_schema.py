"""initial schema

Revision ID: 20260528_0001
Revises:
Create Date: 2026-05-28
"""

from alembic import op
import sqlalchemy as sa


revision = "20260528_0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "meal_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("people_count", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("remark", sa.Text(), nullable=False),
        sa.Column("cashier_id", sa.Integer(), nullable=False),
        sa.Column("payment_method", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_meal_sessions_number", "meal_sessions", ["number"], unique=True)
    op.create_index("ix_meal_sessions_status", "meal_sessions", ["status"])
    op.create_index("ix_meal_sessions_store_id", "meal_sessions", ["store_id"])

    op.create_table(
        "stores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("merchant_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("business_status", sa.String(length=32), nullable=False),
        sa.Column("business_hours", sa.String(length=64), nullable=False),
        sa.Column("phone", sa.String(length=32), nullable=False),
        sa.Column("address", sa.String(length=255), nullable=False),
        sa.Column("queue_prefix", sa.String(length=8), nullable=False),
        sa.Column("avg_prepare_minutes", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stores_merchant_id", "stores", ["merchant_id"])

    op.create_table(
        "service_calls",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=32), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("source", sa.String(length=24), nullable=False),
        sa.Column("status", sa.String(length=24), nullable=False),
        sa.Column("handled_by", sa.Integer(), nullable=False),
        sa.Column("resolution", sa.Text(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_service_calls_number", "service_calls", ["number"])
    op.create_index("ix_service_calls_status", "service_calls", ["status"])
    op.create_index("ix_service_calls_store_id", "service_calls", ["store_id"])

    op.create_table(
        "operation_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("staff_id", sa.Integer(), nullable=False),
        sa.Column("staff_name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("action", sa.String(length=64), nullable=False),
        sa.Column("target_type", sa.String(length=64), nullable=False),
        sa.Column("target_id", sa.String(length=64), nullable=False),
        sa.Column("detail", sa.Text(), nullable=False),
        sa.Column("created_at", sa.String(length=32), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_operation_logs_action", "operation_logs", ["action"])
    op.create_index("ix_operation_logs_staff_id", "operation_logs", ["staff_id"])
    op.create_index("ix_operation_logs_store_id", "operation_logs", ["store_id"])
    op.create_index("ix_operation_logs_target_id", "operation_logs", ["target_id"])

    op.create_table(
        "line_items",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("session_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("source", sa.String(length=24), nullable=False),
        sa.Column("note", sa.Text(), nullable=False),
        sa.ForeignKeyConstraint(["session_id"], ["meal_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_line_items_session_id", "line_items", ["session_id"])

    op.create_table(
        "dishes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("price", sa.Numeric(12, 2), nullable=False),
        sa.Column("available", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_dishes_store_id", "dishes", ["store_id"])

    op.create_table(
        "staff",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("store_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=80), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.ForeignKeyConstraint(["store_id"], ["stores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_staff_store_id", "staff", ["store_id"])


def downgrade() -> None:
    op.drop_index("ix_staff_store_id", table_name="staff")
    op.drop_table("staff")
    op.drop_index("ix_dishes_store_id", table_name="dishes")
    op.drop_table("dishes")
    op.drop_index("ix_line_items_session_id", table_name="line_items")
    op.drop_table("line_items")
    op.drop_index("ix_operation_logs_target_id", table_name="operation_logs")
    op.drop_index("ix_operation_logs_store_id", table_name="operation_logs")
    op.drop_index("ix_operation_logs_staff_id", table_name="operation_logs")
    op.drop_index("ix_operation_logs_action", table_name="operation_logs")
    op.drop_table("operation_logs")
    op.drop_index("ix_service_calls_store_id", table_name="service_calls")
    op.drop_index("ix_service_calls_status", table_name="service_calls")
    op.drop_index("ix_service_calls_number", table_name="service_calls")
    op.drop_table("service_calls")
    op.drop_index("ix_stores_merchant_id", table_name="stores")
    op.drop_table("stores")
    op.drop_index("ix_meal_sessions_store_id", table_name="meal_sessions")
    op.drop_index("ix_meal_sessions_status", table_name="meal_sessions")
    op.drop_index("ix_meal_sessions_number", table_name="meal_sessions")
    op.drop_table("meal_sessions")
