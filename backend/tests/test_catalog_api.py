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


def test_store_catalog_endpoint_returns_store_dishes_and_staff():
    response = client.get("/api/stores/1/catalog")

    assert response.status_code == 200
    payload = response.json()
    assert payload["store"]["name"] == "川香麻辣烫（中山店）"
    assert payload["store"]["business_status"] == "open"
    assert [dish["name"] for dish in payload["dishes"]][:2] == ["招牌麻辣烫", "牛肉串"]
    assert payload["staff"][0]["role"] == "boss"


def test_store_business_status_can_be_updated():
    response = client.patch(
        "/api/stores/1/business-status",
        json={"business_status": "paused"},
        headers=auth_header("李店长"),
    )

    assert response.status_code == 200
    assert response.json()["business_status"] == "paused"

    catalog = client.get("/api/stores/1/catalog").json()
    assert catalog["store"]["business_status"] == "paused"


def test_dish_can_be_created_and_toggled():
    created = client.post(
        "/api/stores/1/dishes",
        json={"name": "酸梅汤", "category": "饮品", "price": "8.00", "available": True},
        headers=auth_header("李店长"),
    )

    assert created.status_code == 201
    assert created.json()["name"] == "酸梅汤"
    dish_id = created.json()["id"]

    updated = client.patch(
        f"/api/dishes/{dish_id}",
        json={"available": False, "price": "7.00"},
        headers=auth_header("李店长"),
    )

    assert updated.status_code == 200
    assert updated.json()["available"] is False
    assert updated.json()["price"] == "7.00"

    catalog = client.get("/api/stores/1/catalog").json()
    matching = [dish for dish in catalog["dishes"] if dish["name"] == "酸梅汤"]
    assert matching[0]["available"] is False


def test_platform_overview_endpoint_returns_review_and_plan_cards():
    response = client.get("/api/platform/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["pending_merchants"] >= 0
    assert payload["plans"][0]["name"] == "免费版"
