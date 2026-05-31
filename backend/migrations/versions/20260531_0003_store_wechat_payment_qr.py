"""add store wechat payment qr

Revision ID: 20260531_0003
Revises: 20260529_0002
Create Date: 2026-05-31
"""

from alembic import op
import sqlalchemy as sa


revision = "20260531_0003"
down_revision = "20260529_0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("stores", sa.Column("payment_qr", sa.String(length=255), nullable=False, server_default="微信收款码"))
    op.add_column("stores", sa.Column("wechat_payment_qr_url", sa.String(length=500), nullable=False, server_default=""))
    op.add_column("stores", sa.Column("wechat_payment_qr_name", sa.String(length=120), nullable=False, server_default=""))


def downgrade() -> None:
    op.drop_column("stores", "wechat_payment_qr_name")
    op.drop_column("stores", "wechat_payment_qr_url")
    op.drop_column("stores", "payment_qr")
