from fastapi.testclient import TestClient

from app.api.routes import get_auth_repository, get_catalog_repository, get_operation_log_repository, get_repository, get_service_call_repository
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

    def override_service_call_repository():
        with session_factory() as db:
            yield ServiceCallRepository(db)

    def override_auth_repository():
        with session_factory() as db:
            yield AuthRepository(db)

    def override_operation_log_repository():
        with session_factory() as db:
            yield OperationLogRepository(db)

    app.dependency_overrides[get_repository] = override_repository
    app.dependency_overrides[get_catalog_repository] = override_catalog_repository
    app.dependency_overrides[get_service_call_repository] = override_service_call_repository
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


def test_manager_can_update_store_settings_and_staff_status():
    response = client.patch(
        "/api/stores/1/settings",
        json={
            "business_hours": "09:00-21:30",
            "address": "中山市东区新地址",
            "queue_prefix": "b",
            "avg_prepare_minutes": 25,
            "payment_qr": "中山店老板微信收款码",
        },
        headers=auth_header("李店长"),
    )
    assert response.status_code == 200
    assert response.json()["queue_prefix"] == "B"
    assert response.json()["business_hours"] == "09:00-21:30"
    assert response.json()["payment_qr"] == "中山店老板微信收款码"

    staff_update = client.patch(
        "/api/staff/4/status",
        json={"status": "inactive"},
        headers=auth_header("李店长"),
    )
    assert staff_update.status_code == 200
    assert staff_update.json()["status"] == "inactive"


def test_boss_can_configure_wechat_payment_qr_and_catalog_exposes_it():
    response = client.patch(
        "/api/stores/1/payment-qr",
        json={
            "wechat_payment_qr_url": "https://cdn.example.com/store-1/wechat-pay.jpg",
            "wechat_payment_qr_name": "中山店微信收款码",
        },
        headers=auth_header("张老板"),
    )

    assert response.status_code == 200
    assert response.json()["wechat_payment_qr_url"] == "https://cdn.example.com/store-1/wechat-pay.jpg"
    assert response.json()["wechat_payment_qr_name"] == "中山店微信收款码"

    catalog = client.get("/api/stores/1/catalog").json()
    assert catalog["store"]["wechat_payment_qr_url"] == "https://cdn.example.com/store-1/wechat-pay.jpg"
    assert catalog["store"]["wechat_payment_qr_name"] == "中山店微信收款码"


def test_manager_cannot_configure_wechat_payment_qr():
    response = client.patch(
        "/api/stores/1/payment-qr",
        json={
            "wechat_payment_qr_url": "https://cdn.example.com/store-1/manager-pay.jpg",
            "wechat_payment_qr_name": "店长试改",
        },
        headers=auth_header("李店长"),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "role is not allowed"


def test_staff_status_update_rejects_cross_store_access():
    client.post(
        "/api/stores/2/catalog",
        headers=auth_header("李店长"),
    )
    response = client.patch(
        "/api/staff/4/status",
        json={"status": "inactive"},
        headers=auth_header("李店长", store_id=2),
    )
    assert response.status_code in {403, 404}
