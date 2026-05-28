from fastapi.testclient import TestClient

from app.api.routes import (
    get_auth_repository,
    get_catalog_repository,
    get_operation_log_repository,
    get_repository,
    get_service_call_repository,
)
from app.db.base import Base
from app.db.session import create_session_factory, create_sqlite_engine
from app.main import app
from app.repositories.auth import AuthRepository
from app.repositories.catalog import CatalogRepository
from app.repositories.meal_sessions import MealSessionRepository
from app.repositories.operation_logs import OperationLogRepository
from app.repositories.service_calls import ServiceCallRepository


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

    def override_service_call_repository():
        with session_factory() as db:
            yield ServiceCallRepository(db)

    def override_operation_log_repository():
        with session_factory() as db:
            yield OperationLogRepository(db)

    app.dependency_overrides[get_repository] = override_repository
    app.dependency_overrides[get_catalog_repository] = override_catalog_repository
    app.dependency_overrides[get_auth_repository] = override_auth_repository
    app.dependency_overrides[get_service_call_repository] = override_service_call_repository
    app.dependency_overrides[get_operation_log_repository] = override_operation_log_repository


def auth_header(staff_name: str, store_id: int = 1) -> dict:
    client.get(f"/api/stores/{store_id}/catalog")
    response = client.post(
        "/api/auth/login",
        json={"store_id": store_id, "staff_name": staff_name, "pin": "0000"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_staff_queue_actions_reject_cross_store_session():
    store_2_manager = auth_header("李店长", store_id=2)
    store_1_manager = auth_header("李店长", store_id=1)
    issued = client.post(
        "/api/stores/2/queue/issue",
        json={"people_count": 2, "remark": "二店"},
        headers=store_2_manager,
    )
    assert issued.status_code == 201

    response = client.post(
        f"/api/meal-sessions/{issued.json()['number']}/actions/start-preparing",
        headers=store_1_manager,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "staff cannot access this store"


def test_staff_cannot_edit_dish_from_another_store():
    store_1_manager = auth_header("李店长", store_id=1)
    store_2_manager = auth_header("李店长", store_id=2)
    created = client.post(
        "/api/stores/2/dishes",
        json={"name": "二店冰粉", "category": "饮品", "price": "6.00", "available": True},
        headers=store_2_manager,
    )
    assert created.status_code == 201

    response = client.patch(
        f"/api/dishes/{created.json()['id']}",
        json={"price": "5.00"},
        headers=store_1_manager,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "staff cannot access this store"


def test_staff_cannot_handle_service_call_from_another_store():
    store_2_manager = auth_header("李店长", store_id=2)
    store_1_cashier = auth_header("王收银", store_id=1)
    issued = client.post(
        "/api/stores/2/queue/issue",
        json={"people_count": 1},
        headers=store_2_manager,
    )
    assert issued.status_code == 201
    service_call = client.post(
        f"/api/meal-sessions/{issued.json()['number']}/service-calls",
        json={"message": "二店需要蘸料", "source": "customer"},
    )
    assert service_call.status_code == 201

    response = client.post(
        f"/api/service-calls/{service_call.json()['id']}/handle",
        json={"staff_id": 3, "resolution": "已处理"},
        headers=store_1_cashier,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "staff cannot access this store"
