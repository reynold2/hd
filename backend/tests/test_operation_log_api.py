from fastapi.testclient import TestClient

from app.api.routes import (
    get_auth_repository,
    get_catalog_repository,
    get_operation_log_repository,
    get_repository,
)
from app.db.base import Base
from app.db.session import create_session_factory, create_sqlite_engine
from app.main import app
from app.repositories.auth import AuthRepository
from app.repositories.catalog import CatalogRepository
from app.repositories.meal_sessions import MealSessionRepository
from app.repositories.operation_logs import OperationLogRepository


client = TestClient(app)


def setup_function():
    engine = create_sqlite_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    session_factory = create_session_factory(engine)

    def override_repository():
        with session_factory() as db:
            yield MealSessionRepository(db)

    def override_catalog_repository():
        with session_factory() as db:
            yield CatalogRepository(db)

    def override_auth_repository():
        with session_factory() as db:
            yield AuthRepository(db)

    def override_operation_log_repository():
        with session_factory() as db:
            yield OperationLogRepository(db)

    app.dependency_overrides[get_repository] = override_repository
    app.dependency_overrides[get_catalog_repository] = override_catalog_repository
    app.dependency_overrides[get_auth_repository] = override_auth_repository
    app.dependency_overrides[get_operation_log_repository] = override_operation_log_repository


def auth_header(staff_name: str, store_id: int = 1) -> dict:
    client.get(f"/api/stores/{store_id}/catalog")
    response = client.post(
        "/api/auth/login",
        json={"store_id": store_id, "staff_name": staff_name, "pin": "0000"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_key_staff_actions_write_operation_logs():
    manager = auth_header("李店长")
    cashier = auth_header("王收银")

    issued = client.post(
        "/api/stores/1/queue/issue",
        json={"people_count": 2, "remark": "少辣"},
        headers=manager,
    )
    assert issued.status_code == 201

    client.post(f"/api/meal-sessions/{issued.json()['number']}/actions/request-checkout")
    paid = client.post(
        f"/api/meal-sessions/{issued.json()['number']}/actions/confirm-payment",
        json={"payment_method": "store_qr", "cashier_id": 3},
        headers=cashier,
    )
    assert paid.status_code == 200

    logs = client.get("/api/stores/1/operation-logs", headers=manager)
    assert logs.status_code == 200
    assert [
        (row["action"], row["target_type"], row["target_id"], row["staff_name"])
        for row in logs.json()
    ] == [
        ("queue.issue", "meal_session", issued.json()["number"], "李店长"),
        ("payment.confirm", "meal_session", issued.json()["number"], "王收银"),
    ]


def test_operation_logs_are_store_scoped():
    client.get("/api/stores/2/catalog")

    response = client.get("/api/stores/2/operation-logs", headers=auth_header("李店长", store_id=1))

    assert response.status_code == 403
    assert response.json()["detail"] == "staff cannot access this store"
