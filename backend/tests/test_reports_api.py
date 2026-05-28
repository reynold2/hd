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


def test_platform_overview_route_returns_summary():
    response = client.get("/api/platform/overview")

    assert response.status_code == 200
    payload = response.json()
    assert payload["merchant_count"] >= 1
    assert payload["store_count"] >= 1
    assert payload["today_sessions"] >= 0
