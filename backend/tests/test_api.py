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
from app.repositories.catalog import CatalogRepository
from app.repositories.meal_sessions import MealSessionRepository
from app.repositories.auth import AuthRepository
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


def test_health_route_returns_ok():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_meal_session_api_supports_main_business_flow():
    created = client.post(
        "/api/meal-sessions",
        json={"store_id": 1, "number": "A018", "people_count": 2, "remark": "少辣，不要葱"},
    )
    assert created.status_code == 201
    assert created.json()["status"] == "occupied"

    add_item = client.post(
        "/api/meal-sessions/A018/items",
        json={"name": "称重菜篮", "amount": "28.00", "source": "staff", "quantity": 1},
    )
    assert add_item.status_code == 200
    assert add_item.json()["total_amount"] == "28.00"

    client.post("/api/meal-sessions/A018/actions/start-preparing")
    client.post("/api/meal-sessions/A018/actions/call")
    client.post("/api/meal-sessions/A018/actions/mark-dining")

    customer_add = client.post(
        "/api/meal-sessions/A018/items",
        json={"name": "可乐", "amount": "5.00", "source": "customer", "quantity": 2},
    )
    assert customer_add.status_code == 200
    assert customer_add.json()["total_amount"] == "38.00"

    checkout = client.post("/api/meal-sessions/A018/actions/request-checkout")
    assert checkout.status_code == 200
    assert checkout.json()["status"] == "checkout_requested"

    paid = client.post(
        "/api/meal-sessions/A018/actions/confirm-payment",
        json={"payment_method": "store_qr", "cashier_id": 7},
        headers=auth_header("王收银"),
    )
    assert paid.status_code == 200
    assert paid.json()["status"] == "paid"

    completed = client.post("/api/meal-sessions/A018/actions/complete", headers=auth_header("王收银"))
    assert completed.status_code == 200
    assert completed.json()["status"] == "completed"


def test_store_queue_lists_active_sessions_only():
    client.post(
        "/api/meal-sessions",
        json={"store_id": 1, "number": "A030", "people_count": 2},
    )
    client.post(
        "/api/meal-sessions",
        json={"store_id": 1, "number": "A031", "people_count": 1},
    )
    client.post("/api/meal-sessions/A031/actions/start-preparing")
    client.post("/api/meal-sessions/A031/actions/call")
    client.post("/api/meal-sessions/A031/actions/mark-dining")
    client.post("/api/meal-sessions/A031/actions/request-checkout")
    client.post(
        "/api/meal-sessions/A031/actions/confirm-payment",
        json={"payment_method": "store_qr", "cashier_id": 7},
        headers=auth_header("王收银"),
    )
    client.post("/api/meal-sessions/A031/actions/complete", headers=auth_header("王收银"))

    response = client.get("/api/stores/1/queue")

    assert response.status_code == 200
    assert [row["number"] for row in response.json()] == ["A030"]


def test_store_can_issue_next_queue_number_and_list_cashier_pending():
    issued = client.post(
        "/api/stores/1/queue/issue",
        json={"people_count": 2, "remark": "少辣，不要葱"},
        headers=auth_header("李店长"),
    )

    assert issued.status_code == 201
    assert issued.json()["number"] == "A001"
    assert issued.json()["status"] == "occupied"

    client.post("/api/meal-sessions/A001/actions/start-preparing")
    client.post("/api/meal-sessions/A001/actions/call")
    client.post("/api/meal-sessions/A001/actions/mark-dining")
    client.post(
        "/api/meal-sessions/A001/items",
        json={"name": "酸梅汤", "amount": "8.00", "source": "customer", "quantity": 1},
    )
    client.post("/api/meal-sessions/A001/actions/request-checkout")

    pending = client.get("/api/stores/1/cashier/pending")

    assert pending.status_code == 200
    assert pending.json()[0]["number"] == "A001"
    assert pending.json()[0]["total_amount"] == "8.00"


def test_customer_add_item_and_cashier_complete_releases_number():
    client.post(
        "/api/stores/1/queue/issue",
        json={"people_count": 1, "remark": ""},
        headers=auth_header("李店长"),
    )
    add_item = client.post(
        "/api/meal-sessions/A001/items",
        json={"name": "冰粉", "amount": "6.00", "source": "customer", "quantity": 1},
    )
    assert add_item.status_code == 200
    assert add_item.json()["total_amount"] == "6.00"

    client.post("/api/meal-sessions/A001/actions/request-checkout")
    client.post(
        "/api/meal-sessions/A001/actions/confirm-payment",
        json={"payment_method": "store_qr", "cashier_id": 1},
        headers=auth_header("王收银"),
    )
    client.post("/api/meal-sessions/A001/actions/complete", headers=auth_header("王收银"))

    active = client.get("/api/stores/1/queue").json()
    assert active == []


def test_customer_can_append_remark_and_call_service_until_payment():
    client.post(
        "/api/meal-sessions",
        json={"store_id": 1, "number": "A050", "people_count": 2, "remark": "少辣"},
    )

    remark = client.post(
        "/api/meal-sessions/A050/remarks",
        json={"remark": "加麻加汤", "source": "customer"},
    )
    assert remark.status_code == 200
    assert remark.json()["remark"] == "少辣\ncustomer: 加麻加汤"

    service_call = client.post(
        "/api/meal-sessions/A050/service-calls",
        json={"message": "麻烦加一份蘸料", "source": "customer"},
    )
    assert service_call.status_code == 201
    assert service_call.json()["number"] == "A050"
    assert service_call.json()["store_id"] == 1
    assert service_call.json()["status"] == "pending"

    pending = client.get("/api/stores/1/service-calls/pending")
    assert pending.status_code == 200
    assert [row["message"] for row in pending.json()] == ["麻烦加一份蘸料"]

    handled = client.post(
        f"/api/service-calls/{service_call.json()['id']}/handle",
        json={"staff_id": 2, "resolution": "已加蘸料"},
        headers=auth_header("李店长"),
    )
    assert handled.status_code == 200
    assert handled.json()["status"] == "handled"
    assert handled.json()["handled_by"] == 2
    assert handled.json()["resolution"] == "已加蘸料"

    assert client.get("/api/stores/1/service-calls/pending").json() == []


def test_closed_session_rejects_remark_and_service_call():
    client.post(
        "/api/meal-sessions",
        json={"store_id": 1, "number": "A051", "people_count": 1},
    )
    client.post("/api/meal-sessions/A051/actions/request-checkout")
    client.post(
        "/api/meal-sessions/A051/actions/confirm-payment",
        json={"payment_method": "store_qr", "cashier_id": 1},
        headers=auth_header("王收银"),
    )

    remark = client.post(
        "/api/meal-sessions/A051/remarks",
        json={"remark": "加汤", "source": "customer"},
    )
    assert remark.status_code == 400
    assert remark.json()["detail"] == "cannot update a closed session"

    service_call = client.post(
        "/api/meal-sessions/A051/service-calls",
        json={"message": "需要帮助", "source": "customer"},
    )
    assert service_call.status_code == 400
    assert service_call.json()["detail"] == "cannot call service for a closed session"


def test_queue_extension_actions_support_skip_resume_cancel_and_risk():
    client.post(
        "/api/meal-sessions",
        json={"store_id": 1, "number": "A040", "people_count": 2},
    )
    manager = auth_header("李店长")
    client.post("/api/meal-sessions/A040/actions/start-preparing", headers=manager)
    client.post("/api/meal-sessions/A040/actions/call", headers=manager)

    skipped = client.post("/api/meal-sessions/A040/actions/skip", headers=manager)
    assert skipped.status_code == 200
    assert skipped.json()["status"] == "skipped"

    resumed = client.post("/api/meal-sessions/A040/actions/resume", headers=manager)
    assert resumed.status_code == 200
    assert resumed.json()["status"] == "preparing"

    risk = client.post("/api/meal-sessions/A040/actions/mark-unpaid-risk", headers=manager)
    assert risk.status_code == 200
    assert risk.json()["status"] == "risk_unpaid"

    cancelled = client.post("/api/meal-sessions/A040/actions/cancel", headers=manager)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"

    active = client.get("/api/stores/1/queue").json()
    assert active == []


def test_queue_extension_actions_reject_invalid_states():
    client.post(
        "/api/meal-sessions",
        json={"store_id": 1, "number": "A041", "people_count": 2},
    )
    manager = auth_header("李店长")

    resume = client.post("/api/meal-sessions/A041/actions/resume", headers=manager)
    assert resume.status_code == 400
    assert "expected skipped" in resume.json()["detail"]

    client.post("/api/meal-sessions/A041/actions/request-checkout")
    client.post(
        "/api/meal-sessions/A041/actions/confirm-payment",
        json={"payment_method": "store_qr", "cashier_id": 1},
        headers=auth_header("王收银"),
    )

    cancel = client.post("/api/meal-sessions/A041/actions/cancel", headers=manager)
    assert cancel.status_code == 400
    assert cancel.json()["detail"] == "cannot cancel a paid session"
