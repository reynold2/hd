from sqlalchemy import func, select

from app.db.base import Base
from app.db.models import (
    DishModel,
    MealSessionModel,
    OperationLogModel,
    RoleBindingModel,
    ServiceCallModel,
    StaffModel,
    StoreModel,
)
from app.db.session import create_session_factory, create_sqlite_engine
from app.seed_data import seed_demo_data


def test_seed_demo_data_creates_complete_store_dataset_idempotently():
    engine = create_sqlite_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        seed_demo_data(db)
        seed_demo_data(db)

        store = db.get(StoreModel, 1)
        assert store.name == "川香麻辣烫（中山店）"
        assert store.business_status == "open"

        assert db.scalar(select(func.count()).select_from(DishModel)) == 8
        assert db.scalar(select(func.count()).select_from(StaffModel)) == 5
        assert db.scalar(select(func.count()).select_from(RoleBindingModel)) == 5
        assert db.scalar(select(func.count()).select_from(MealSessionModel)) == 8
        assert db.scalar(select(func.count()).select_from(ServiceCallModel)) == 1
        assert db.scalar(select(func.count()).select_from(OperationLogModel)) == 4

        customer = db.scalar(
            select(RoleBindingModel).where(RoleBindingModel.openid == "openid_customer_001")
        )
        assert customer.role == "customer"
        assert customer.store_id == 1

        checkout = db.scalar(select(MealSessionModel).where(MealSessionModel.number == "A022"))
        assert checkout.status == "checkout_requested"
        assert len(checkout.items) > 0
