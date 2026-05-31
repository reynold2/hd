from __future__ import annotations

from typing import List

from sqlalchemy import ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class MealSessionModel(Base):
    __tablename__ = "meal_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    number: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    people_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(32), index=True)
    remark: Mapped[str] = mapped_column(Text, default="")
    cashier_id: Mapped[int] = mapped_column(Integer, default=0)
    payment_method: Mapped[str] = mapped_column(String(32), default="")

    items: Mapped[List["LineItemModel"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="LineItemModel.id",
    )


class LineItemModel(Base):
    __tablename__ = "line_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("meal_sessions.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    amount: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    source: Mapped[str] = mapped_column(String(24))
    note: Mapped[str] = mapped_column(Text, default="")

    session: Mapped[MealSessionModel] = relationship(back_populates="items")


class ServiceCallModel(Base):
    __tablename__ = "service_calls"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    number: Mapped[str] = mapped_column(String(32), index=True)
    message: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(24), default="customer")
    status: Mapped[str] = mapped_column(String(24), default="pending", index=True)
    handled_by: Mapped[int] = mapped_column(Integer, default=0)
    resolution: Mapped[str] = mapped_column(Text, default="")


class OperationLogModel(Base):
    __tablename__ = "operation_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    staff_id: Mapped[int] = mapped_column(Integer, index=True)
    staff_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(32))
    action: Mapped[str] = mapped_column(String(64), index=True)
    target_type: Mapped[str] = mapped_column(String(64))
    target_id: Mapped[str] = mapped_column(String(64), index=True)
    detail: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[str] = mapped_column(String(32), default="")


class StoreModel(Base):
    __tablename__ = "stores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    merchant_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str] = mapped_column(String(120))
    business_status: Mapped[str] = mapped_column(String(32), default="open")
    business_hours: Mapped[str] = mapped_column(String(64), default="10:00-22:30")
    phone: Mapped[str] = mapped_column(String(32), default="")
    address: Mapped[str] = mapped_column(String(255), default="")
    queue_prefix: Mapped[str] = mapped_column(String(8), default="A")
    avg_prepare_minutes: Mapped[int] = mapped_column(Integer, default=18)
    payment_qr: Mapped[str] = mapped_column(String(255), default="微信收款码")
    wechat_payment_qr_url: Mapped[str] = mapped_column(String(500), default="")
    wechat_payment_qr_name: Mapped[str] = mapped_column(String(120), default="")

    dishes: Mapped[List["DishModel"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
        order_by="DishModel.id",
    )
    staff: Mapped[List["StaffModel"]] = relationship(
        back_populates="store",
        cascade="all, delete-orphan",
        order_by="StaffModel.id",
    )


class DishModel(Base):
    __tablename__ = "dishes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(120))
    category: Mapped[str] = mapped_column(String(32), default="推荐")
    price: Mapped[Numeric] = mapped_column(Numeric(12, 2))
    available: Mapped[int] = mapped_column(Integer, default=1)

    store: Mapped[StoreModel] = relationship(back_populates="dishes")


class StaffModel(Base):
    __tablename__ = "staff"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    store_id: Mapped[int] = mapped_column(ForeignKey("stores.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(32))
    status: Mapped[str] = mapped_column(String(32), default="active")

    store: Mapped[StoreModel] = relationship(back_populates="staff")


class RoleBindingModel(Base):
    __tablename__ = "role_bindings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    display_name: Mapped[str] = mapped_column(String(80))
    role: Mapped[str] = mapped_column(String(32), index=True)
    store_id: Mapped[int] = mapped_column(Integer, index=True)
    openid: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    enabled: Mapped[int] = mapped_column(Integer, default=1)
