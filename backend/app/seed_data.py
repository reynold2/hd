from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.base import Base
from app.db.models import (
    DishModel,
    LineItemModel,
    MealSessionModel,
    OperationLogModel,
    RoleBindingModel,
    ServiceCallModel,
    StaffModel,
    StoreModel,
)
from app.db.session import create_session_factory, create_sqlite_engine


STORE_ID = 1


def seed_demo_data(db: Session) -> None:
    seed_store(db)
    seed_dishes(db)
    seed_staff(db)
    seed_role_bindings(db)
    seed_meal_sessions(db)
    seed_service_calls(db)
    seed_operation_logs(db)
    db.commit()


def seed_store(db: Session) -> None:
    store = db.get(StoreModel, STORE_ID)
    if store is None:
        store = StoreModel(id=STORE_ID, merchant_id=1)
        db.add(store)
    store.name = "川香麻辣烫（中山店）"
    store.business_status = "open"
    store.business_hours = "10:00-22:30"
    store.phone = "0760-12345678"
    store.address = "中山市东区中山三路88号"
    store.queue_prefix = "A"
    store.avg_prepare_minutes = 20
    store.payment_qr = "川香麻辣烫（中山店）微信收款码"
    store.wechat_payment_qr_url = "/static/payment-qrs/store-1-wechat-pay.jpg"
    store.wechat_payment_qr_name = "川香麻辣烫（中山店）微信收款码"
    db.flush()


def seed_dishes(db: Session) -> None:
    dishes = [
        ("招牌麻辣烫", "推荐", "12.00", True),
        ("牛肉串", "荤菜", "15.00", True),
        ("肥牛卷", "荤菜", "18.00", True),
        ("金针菇", "素菜", "3.00", True),
        ("娃娃菜", "素菜", "4.00", True),
        ("宽粉", "主食", "2.00", True),
        ("手工面", "主食", "5.00", True),
        ("冰粉", "饮品", "6.00", True),
    ]
    for name, category, price, available in dishes:
        dish = db.scalar(
            select(DishModel).where(DishModel.store_id == STORE_ID).where(DishModel.name == name)
        )
        if dish is None:
            dish = DishModel(store_id=STORE_ID, name=name)
            db.add(dish)
        dish.category = category
        dish.price = Decimal(price)
        dish.available = 1 if available else 0


def seed_staff(db: Session) -> None:
    staff_members = [
        ("张老板", "boss"),
        ("李店长", "manager"),
        ("周服务", "staff"),
        ("赵师傅", "cook"),
        ("王收银", "cashier"),
    ]
    for name, role in staff_members:
        staff = db.scalar(
            select(StaffModel).where(StaffModel.store_id == STORE_ID).where(StaffModel.name == name)
        )
        if staff is None:
            staff = StaffModel(store_id=STORE_ID, name=name)
            db.add(staff)
        staff.role = role
        staff.status = "active"


def seed_role_bindings(db: Session) -> None:
    bindings = [
        (5, "顾客测试号", "customer", "openid_customer_001"),
        (6, "小程序老板", "boss", "openid_boss_001"),
        (7, "小程序服务员", "staff", "openid_staff_001"),
        (8, "小程序制作", "kitchen", "openid_kitchen_001"),
        (9, "小程序收银", "cashier", "openid_cashier_001"),
    ]
    for user_id, display_name, role, openid in bindings:
        binding = db.scalar(select(RoleBindingModel).where(RoleBindingModel.openid == openid))
        if binding is None:
            binding = RoleBindingModel(openid=openid)
            db.add(binding)
        binding.user_id = user_id
        binding.display_name = display_name
        binding.role = role
        binding.store_id = STORE_ID
        binding.enabled = 1


def seed_meal_sessions(db: Session) -> None:
    sessions = [
        ("A018", "preparing", 2, "少辣，不要葱", [("招牌麻辣烫", "12.00", 1), ("宽粉", "2.00", 1), ("牛肉串", "15.00", 1)]),
        ("A019", "occupied", 1, "微辣，加香菜", [("招牌麻辣烫", "12.00", 1), ("娃娃菜", "4.00", 1)]),
        ("A020", "called", 3, "打包一份", [("肥牛卷", "18.00", 1), ("手工面", "5.00", 2)]),
        ("A021", "dining", 2, "堂食", [("招牌麻辣烫", "12.00", 2), ("冰粉", "6.00", 2)]),
        ("A022", "checkout_requested", 4, "需要开发票", [("牛肉串", "15.00", 2), ("宽粉", "2.00", 2)]),
        ("A023", "paid", 2, "已支付待释放", [("招牌麻辣烫", "12.00", 1), ("冰粉", "6.00", 1)]),
        ("A024", "skipped", 1, "顾客暂离", [("金针菇", "3.00", 1), ("手工面", "5.00", 1)]),
        ("A025", "cancelled", 1, "顾客取消", [("娃娃菜", "4.00", 1)]),
    ]
    for number, status, people_count, remark, items in sessions:
        session = db.scalar(select(MealSessionModel).where(MealSessionModel.number == number))
        if session is None:
            session = MealSessionModel(number=number)
            db.add(session)
        session.store_id = STORE_ID
        session.people_count = people_count
        session.status = status
        session.remark = remark
        session.payment_method = "store_qr" if status == "paid" else ""
        session.cashier_id = 5 if status == "paid" else 0
        session.items.clear()
        db.flush()
        for name, amount, quantity in items:
            session.items.append(
                LineItemModel(
                    name=name,
                    amount=Decimal(amount),
                    quantity=quantity,
                    source="customer",
                    note="演示数据",
                )
            )


def seed_service_calls(db: Session) -> None:
    call = db.scalar(
        select(ServiceCallModel)
        .where(ServiceCallModel.store_id == STORE_ID)
        .where(ServiceCallModel.number == "A021")
        .where(ServiceCallModel.message == "需要加汤和餐巾纸")
    )
    if call is None:
        call = ServiceCallModel(store_id=STORE_ID, number="A021", message="需要加汤和餐巾纸")
        db.add(call)
    call.source = "customer"
    call.status = "pending"
    call.handled_by = 0
    call.resolution = ""


def seed_operation_logs(db: Session) -> None:
    logs = [
        ("issue", "meal_session", "A018", "李店长", "manager", "发放号码 A018"),
        ("start_preparing", "meal_session", "A018", "赵师傅", "cook", "开始制作 A018"),
        ("request_checkout", "meal_session", "A022", "顾客测试号", "customer", "顾客呼叫结账"),
        ("confirm_payment", "meal_session", "A023", "王收银", "cashier", "确认收款"),
    ]
    for action, target_type, target_id, staff_name, role, detail in logs:
        log = db.scalar(
            select(OperationLogModel)
            .where(OperationLogModel.store_id == STORE_ID)
            .where(OperationLogModel.action == action)
            .where(OperationLogModel.target_id == target_id)
        )
        if log is None:
            log = OperationLogModel(store_id=STORE_ID, action=action, target_id=target_id)
            db.add(log)
        log.staff_id = 0
        log.staff_name = staff_name
        log.role = role
        log.target_type = target_type
        log.detail = detail
        log.created_at = "2026-05-29 10:00:00"


def main() -> None:
    engine = create_sqlite_engine()
    Base.metadata.create_all(bind=engine)
    session_factory = create_session_factory(engine)
    with session_factory() as db:
        seed_demo_data(db)
    print("Demo seed data written to database")


if __name__ == "__main__":
    main()
