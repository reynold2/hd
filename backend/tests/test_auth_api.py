from fastapi.testclient import TestClient

from app.api.routes import get_auth_repository, get_catalog_repository, get_repository
from app.db.base import Base
from app.db.session import create_session_factory, create_sqlite_engine
from app.main import app
from app.repositories.auth import AuthRepository
from app.repositories.catalog import CatalogRepository
from app.repositories.meal_sessions import MealSessionRepository


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

    app.dependency_overrides[get_repository] = override_repository
    app.dependency_overrides[get_catalog_repository] = override_catalog_repository
    app.dependency_overrides[get_auth_repository] = override_auth_repository


def auth_header(staff_name: str, store_id: int = 1) -> dict:
    client.get(f"/api/stores/{store_id}/catalog")
    response = client.post(
        "/api/auth/login",
        json={"store_id": store_id, "staff_name": staff_name, "pin": "0000"},
    )
    assert response.status_code == 200
    return {"Authorization": f"Bearer {response.json()['token']}"}


def test_staff_can_login_and_receive_role_context():
    client.get("/api/stores/1/catalog")

    response = client.post(
        "/api/auth/login",
        json={"store_id": 1, "staff_name": "李店长", "pin": "0000"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["token"]
    assert payload["staff"]["store_id"] == 1
    assert payload["staff"]["role"] == "manager"


def test_protected_merchant_action_requires_login():
    response = client.post("/api/stores/1/queue/issue", json={"people_count": 2})

    assert response.status_code == 401
    assert response.json()["detail"] == "authentication required"


def test_role_rejects_cashier_from_store_configuration():
    response = client.patch(
        "/api/stores/1/business-status",
        json={"business_status": "paused"},
        headers=auth_header("王收银"),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "role is not allowed"


def test_cross_store_access_is_rejected():
    client.get("/api/stores/2/catalog")

    response = client.post(
        "/api/stores/2/queue/issue",
        json={"people_count": 2},
        headers=auth_header("李店长", store_id=1),
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "staff cannot access this store"
