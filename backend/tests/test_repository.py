from decimal import Decimal

from app.db.base import Base
from app.db.session import create_sqlite_engine, create_session_factory
from app.domain.queue import LineItem, MealSession, QueueStatus
from app.repositories.meal_sessions import MealSessionRepository


def test_repository_persists_meal_session_with_items(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'queue.db'}"
    engine = create_sqlite_engine(database_url)
    Base.metadata.create_all(bind=engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        repository = MealSessionRepository(db)
        session = MealSession(number="A018", store_id=1, people_count=2, remark="少辣")
        session.add_item(LineItem(name="称重菜篮", amount=Decimal("28.00"), source="staff"))
        session.add_item(LineItem(name="可乐", amount=Decimal("5.00"), quantity=2, source="customer"))
        repository.save(session)

    with session_factory() as db:
        repository = MealSessionRepository(db)
        loaded = repository.get("A018")

    assert loaded is not None
    assert loaded.number == "A018"
    assert loaded.status == QueueStatus.OCCUPIED
    assert loaded.total_amount == Decimal("38.00")
    assert loaded.remark == "少辣"
    assert [item.name for item in loaded.items] == ["称重菜篮", "可乐"]


def test_repository_updates_existing_meal_session(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'queue.db'}"
    engine = create_sqlite_engine(database_url)
    Base.metadata.create_all(bind=engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        repository = MealSessionRepository(db)
        session = MealSession(number="A019", store_id=1, people_count=1)
        repository.save(session)
        session.start_preparing()
        session.call_for_pickup()
        session.mark_dining()
        session.request_checkout()
        session.confirm_payment(payment_method="store_qr", cashier_id=8)
        repository.save(session)

    with session_factory() as db:
        loaded = MealSessionRepository(db).get("A019")

    assert loaded is not None
    assert loaded.status == QueueStatus.PAID
    assert loaded.payment_method == "store_qr"
    assert loaded.cashier_id == 8


def test_repository_lists_active_sessions_by_store(tmp_path):
    database_url = f"sqlite:///{tmp_path / 'queue.db'}"
    engine = create_sqlite_engine(database_url)
    Base.metadata.create_all(bind=engine)
    session_factory = create_session_factory(engine)

    with session_factory() as db:
        repository = MealSessionRepository(db)
        repository.save(MealSession(number="A020", store_id=1, people_count=1))
        repository.save(MealSession(number="A021", store_id=1, people_count=2))
        completed = MealSession(number="A022", store_id=1, people_count=3)
        completed.start_preparing()
        completed.call_for_pickup()
        completed.mark_dining()
        completed.request_checkout()
        completed.confirm_payment(payment_method="store_qr", cashier_id=1)
        completed.complete()
        repository.save(completed)

    with session_factory() as db:
        active_numbers = [session.number for session in MealSessionRepository(db).list_active(store_id=1)]

    assert active_numbers == ["A020", "A021"]
