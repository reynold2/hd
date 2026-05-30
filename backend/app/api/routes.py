from decimal import Decimal
from typing import Generator, List, Optional, Set

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.db.session import create_session_factory, create_sqlite_engine
from app.domain.queue import LineItem, MealSession, QueueStatus
from app.repositories.auth import AuthRepository, StaffContext
from app.repositories.catalog import CatalogRepository
from app.repositories.meal_sessions import MealSessionRepository
from app.repositories.operation_logs import OperationLogRepository
from app.repositories.service_calls import ServiceCallRepository
from app.services.catalog import get_platform_overview


router = APIRouter()
engine = create_sqlite_engine()
SessionLocal = create_session_factory(engine)


def get_repository() -> Generator[MealSessionRepository, None, None]:
    with SessionLocal() as db:
        yield MealSessionRepository(db)


def get_catalog_repository() -> Generator[CatalogRepository, None, None]:
    with SessionLocal() as db:
        yield CatalogRepository(db)


def get_auth_repository() -> Generator[AuthRepository, None, None]:
    with SessionLocal() as db:
        yield AuthRepository(db)


def get_service_call_repository() -> Generator[ServiceCallRepository, None, None]:
    with SessionLocal() as db:
        yield ServiceCallRepository(db)


def get_operation_log_repository() -> Generator[OperationLogRepository, None, None]:
    with SessionLocal() as db:
        yield OperationLogRepository(db)


def get_current_staff(
    authorization: Optional[str] = Header(default=None),
    repository: AuthRepository = Depends(get_auth_repository),
) -> StaffContext:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="authentication required")
    try:
        return repository.verify_token(authorization[len("Bearer "):].strip())
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


def require_roles(staff: StaffContext, allowed_roles: Set[str]) -> None:
    if staff.role not in allowed_roles:
        raise HTTPException(status_code=403, detail="role is not allowed")


def require_store(staff: StaffContext, store_id: int) -> None:
    if staff.store_id != store_id:
        raise HTTPException(status_code=403, detail="staff cannot access this store")


class CreateMealSessionRequest(BaseModel):
    store_id: int = Field(gt=0)
    number: str
    people_count: int = Field(gt=0)
    remark: str = ""


class IssueQueueNumberRequest(BaseModel):
    people_count: int = Field(gt=0)
    remark: str = ""


class AddLineItemRequest(BaseModel):
    name: str
    amount: Decimal
    source: str
    quantity: int = Field(default=1, gt=0)
    note: str = ""


class LoginRequest(BaseModel):
    store_id: int = Field(gt=0)
    staff_name: str
    pin: str


class AdminLoginRequest(BaseModel):
    username: str
    password: str


class WechatLoginRequest(BaseModel):
    openid: str
    store_id: int = Field(gt=0)


class AppendRemarkRequest(BaseModel):
    remark: str
    source: str = "customer"


class CreateServiceCallRequest(BaseModel):
    message: str
    source: str = "customer"


class HandleServiceCallRequest(BaseModel):
    staff_id: int = Field(gt=0)
    resolution: str = ""


class ConfirmPaymentRequest(BaseModel):
    payment_method: str
    cashier_id: int = Field(gt=0)


class UpdateBusinessStatusRequest(BaseModel):
    business_status: str


class UpdateStoreSettingsRequest(BaseModel):
    business_hours: Optional[str] = None
    address: Optional[str] = None
    queue_prefix: Optional[str] = None
    avg_prepare_minutes: Optional[int] = Field(default=None, gt=0)


class UpdateStaffStatusRequest(BaseModel):
    status: str


class CreateDishRequest(BaseModel):
    name: str
    category: str = "推荐"
    price: Decimal
    available: bool = True


class UpdateDishRequest(BaseModel):
    name: Optional[str] = None
    category: Optional[str] = None
    price: Optional[Decimal] = None
    available: Optional[bool] = None


class LineItemResponse(BaseModel):
    name: str
    amount: str
    quantity: int
    source: str
    note: str
    subtotal: str


class MealSessionResponse(BaseModel):
    store_id: int
    number: str
    people_count: int
    status: str
    remark: str
    total_amount: str
    payment_method: str = ""
    cashier_id: int = 0
    items: List[LineItemResponse]


class StaffResponse(BaseModel):
    id: int
    store_id: int
    name: str
    role: str
    status: str


class LoginResponse(BaseModel):
    token: str
    staff: StaffResponse


class AdminProfileResponse(BaseModel):
    username: str
    displayName: str
    role: str
    storeId: Optional[int] = None
    storeName: Optional[str] = None
    avatarUrl: str = ""


class AdminLoginResponse(BaseModel):
    token: str
    profile: AdminProfileResponse
    redirect: str


class AdminUserPayload(BaseModel):
    username: str
    display_name: str
    password: str = "123456"
    avatar_url: str = ""
    role: str = "staff"
    store_id: Optional[int] = None
    openid: Optional[str] = None
    status: str = "enabled"


class AdminUserResponse(AdminUserPayload):
    id: int


class WechatRoleResponse(BaseModel):
    user_id: int
    display_name: str
    openid: str
    role: str
    store_id: int
    store: dict
    entry_page: str


class ServiceCallResponse(BaseModel):
    id: int
    store_id: int
    number: str
    message: str
    source: str
    status: str
    handled_by: int = 0
    resolution: str = ""


class OperationLogResponse(BaseModel):
    id: int
    store_id: int
    staff_id: int
    staff_name: str
    role: str
    action: str
    target_type: str
    target_id: str
    detail: str = ""
    created_at: str = ""


@router.get("/health")
def health():
    return {"status": "ok"}


@router.post("/api/auth/login", response_model=LoginResponse)
def login(payload: LoginRequest, repository: AuthRepository = Depends(get_auth_repository)):
    try:
        return repository.login(payload.store_id, payload.staff_name, payload.pin)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


ADMIN_ROLE_REDIRECTS = {
    "platform_admin": "/platform",
    "store_owner": "/store",
    "cashier": "/cashier",
    "screen": "/screen",
}

ADMIN_TEST_USERS = [
    {
        "id": 1,
        "username": "admin_platform",
        "display_name": "平台管理员",
        "role": "platform_admin",
        "scope": "platform",
        "store_id": None,
        "openid": None,
        "password": "123456",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 2,
        "username": "boss_store_001",
        "display_name": "中山店老板",
        "role": "store_owner",
        "scope": "store",
        "store_id": 1,
        "openid": None,
        "password": "123456",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 3,
        "username": "cashier_store_001",
        "display_name": "中山店收银",
        "role": "cashier",
        "scope": "store",
        "store_id": 1,
        "openid": None,
        "password": "123456",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 4,
        "username": "screen_store_001",
        "display_name": "中山店大屏",
        "role": "screen",
        "scope": "store",
        "store_id": 1,
        "openid": None,
        "password": "123456",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 5,
        "username": "wx_customer_001",
        "display_name": "顾客测试号",
        "role": "customer",
        "scope": "store",
        "store_id": 1,
        "openid": "openid_customer_001",
        "password": "",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 6,
        "username": "wx_boss_001",
        "display_name": "小程序老板",
        "role": "boss",
        "scope": "store",
        "store_id": 1,
        "openid": "openid_boss_001",
        "password": "",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 7,
        "username": "wx_staff_001",
        "display_name": "小程序服务员",
        "role": "staff",
        "scope": "store",
        "store_id": 1,
        "openid": "openid_staff_001",
        "password": "",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 8,
        "username": "wx_kitchen_001",
        "display_name": "小程序制作",
        "role": "kitchen",
        "scope": "store",
        "store_id": 1,
        "openid": "openid_kitchen_001",
        "password": "",
        "avatar_url": "",
        "status": "enabled",
    },
    {
        "id": 9,
        "username": "wx_cashier_001",
        "display_name": "小程序收银",
        "role": "cashier",
        "scope": "store",
        "store_id": 1,
        "openid": "openid_cashier_001",
        "password": "",
        "avatar_url": "",
        "status": "enabled",
    },
]


def admin_user_payload(user: dict) -> dict:
    return {
        "id": user["id"],
        "username": user["username"],
        "display_name": user["display_name"],
        "password": user.get("password") or "",
        "avatar_url": user.get("avatar_url") or "",
        "role": user["role"],
        "store_id": user.get("store_id"),
        "openid": user.get("openid"),
        "status": user.get("status", "enabled"),
    }


def next_admin_user_id() -> int:
    return max((user["id"] for user in ADMIN_TEST_USERS), default=0) + 1


@router.post("/api/admin/login", response_model=AdminLoginResponse)
def admin_login(payload: AdminLoginRequest, catalog_repository: CatalogRepository = Depends(get_catalog_repository)):
    user = next(
        (
            item
            for item in ADMIN_TEST_USERS
            if item["username"] == payload.username.strip() and item.get("password") == payload.password
        ),
        None,
    )
    if user is None:
        raise HTTPException(status_code=401, detail="账号或密码错误")
    store_name = None
    if user.get("store_id"):
        store_name = catalog_repository.get_catalog(user["store_id"])["store"]["name"]
    return {
        "token": f"token_{user['username']}",
        "profile": {
            "username": user["username"],
            "displayName": user["display_name"],
            "role": user["role"],
            "storeId": user.get("store_id"),
            "storeName": store_name,
            "avatarUrl": user.get("avatar_url") or "",
        },
        "redirect": ADMIN_ROLE_REDIRECTS.get(user["role"], "/"),
    }


@router.get("/api/admin/users", response_model=List[AdminUserResponse])
def list_admin_users():
    return [admin_user_payload(user) for user in ADMIN_TEST_USERS]


@router.post("/api/admin/users", response_model=AdminUserResponse, status_code=status.HTTP_201_CREATED)
def create_admin_user(payload: AdminUserPayload):
    if any(user["username"] == payload.username for user in ADMIN_TEST_USERS):
        raise HTTPException(status_code=409, detail="账号已存在")
    user = payload.dict()
    user["id"] = next_admin_user_id()
    user["scope"] = "store" if user.get("store_id") else "platform"
    ADMIN_TEST_USERS.append(user)
    return admin_user_payload(user)


@router.patch("/api/admin/users/{user_id}", response_model=AdminUserResponse)
def update_admin_user(user_id: int, payload: AdminUserPayload):
    user = next((item for item in ADMIN_TEST_USERS if item["id"] == user_id), None)
    if user is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    user.update(payload.dict())
    user["scope"] = "store" if user.get("store_id") else "platform"
    return admin_user_payload(user)


@router.delete("/api/admin/users/{user_id}")
def delete_admin_user(user_id: int):
    index = next((idx for idx, item in enumerate(ADMIN_TEST_USERS) if item["id"] == user_id), None)
    if index is None:
        raise HTTPException(status_code=404, detail="用户不存在")
    ADMIN_TEST_USERS.pop(index)
    return {"ok": True}


@router.get("/api/roles/resolve", response_model=WechatRoleResponse)
def resolve_role_by_openid(
    openid: str,
    store_id: int = Query(gt=0),
    repository: AuthRepository = Depends(get_auth_repository),
):
    try:
        return repository.resolve_wechat_role(openid, store_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/api/auth/wechat-login", response_model=WechatRoleResponse)
def wechat_login(payload: WechatLoginRequest, repository: AuthRepository = Depends(get_auth_repository)):
    try:
        return repository.wechat_login(payload.openid, payload.store_id)
    except ValueError as exc:
        raise HTTPException(status_code=401, detail=str(exc))


@router.post(
    "/api/meal-sessions",
    response_model=MealSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_meal_session(
    payload: CreateMealSessionRequest,
    repository: MealSessionRepository = Depends(get_repository),
):
    number = payload.number.strip().upper()
    existing = repository.get(number)
    if existing is not None and existing.status != QueueStatus.COMPLETED:
        raise HTTPException(status_code=409, detail="number is already occupied")
    session = MealSession(
        number=number,
        store_id=payload.store_id,
        people_count=payload.people_count,
        remark=payload.remark,
    )
    return serialize_session(repository.save(session))


@router.get("/api/meal-sessions/{number}", response_model=MealSessionResponse)
def get_meal_session(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
):
    return serialize_session(get_session(number, repository))


@router.post("/api/meal-sessions/{number}/items", response_model=MealSessionResponse)
def add_line_item(
    number: str,
    payload: AddLineItemRequest,
    repository: MealSessionRepository = Depends(get_repository),
):
    session = get_session(number, repository)
    try:
        session.add_item(
            LineItem(
                name=payload.name,
                amount=payload.amount,
                source=payload.source,
                quantity=payload.quantity,
                note=payload.note,
            )
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return serialize_session(repository.save(session))


@router.post("/api/meal-sessions/{number}/remarks", response_model=MealSessionResponse)
def append_remark(
    number: str,
    payload: AppendRemarkRequest,
    repository: MealSessionRepository = Depends(get_repository),
):
    session = get_session(number, repository)
    try:
        session.append_remark(payload.remark, payload.source)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return serialize_session(repository.save(session))


@router.post(
    "/api/meal-sessions/{number}/service-calls",
    response_model=ServiceCallResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_service_call(
    number: str,
    payload: CreateServiceCallRequest,
    meal_repository: MealSessionRepository = Depends(get_repository),
    service_call_repository: ServiceCallRepository = Depends(get_service_call_repository),
):
    session = get_session(number, meal_repository)
    if session.status in {QueueStatus.PAID, QueueStatus.COMPLETED, QueueStatus.CANCELLED}:
        raise HTTPException(status_code=400, detail="cannot call service for a closed session")
    try:
        return service_call_repository.create(
            store_id=session.store_id,
            number=session.number,
            message=payload.message,
            source=payload.source,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/meal-sessions/{number}/actions/start-preparing", response_model=MealSessionResponse)
def start_preparing(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cook"})
    return run_staff_action(number, "start_preparing", repository, staff)


@router.post("/api/meal-sessions/{number}/actions/call", response_model=MealSessionResponse)
def call_number(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cook"})
    return run_staff_action(number, "call_for_pickup", repository, staff)


@router.post("/api/meal-sessions/{number}/actions/mark-dining", response_model=MealSessionResponse)
def mark_dining(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cook"})
    return run_staff_action(number, "mark_dining", repository, staff)


@router.post("/api/meal-sessions/{number}/actions/request-checkout", response_model=MealSessionResponse)
def request_checkout(number: str, repository: MealSessionRepository = Depends(get_repository)):
    return run_action(number, "request_checkout", repository)


@router.post("/api/meal-sessions/{number}/actions/confirm-payment", response_model=MealSessionResponse)
def confirm_payment(
    number: str,
    payload: ConfirmPaymentRequest,
    repository: MealSessionRepository = Depends(get_repository),
    operation_logs: OperationLogRepository = Depends(get_operation_log_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cashier"})
    session = get_session_for_staff(number, staff, repository)
    try:
        session.confirm_payment(payload.payment_method, payload.cashier_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    saved = repository.save(session)
    operation_logs.record(
        store_id=saved.store_id,
        staff=staff,
        action="payment.confirm",
        target_type="meal_session",
        target_id=saved.number,
        detail=payload.payment_method,
    )
    return serialize_session(saved)


@router.post("/api/meal-sessions/{number}/actions/complete", response_model=MealSessionResponse)
def complete_session(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cashier"})
    return run_staff_action(number, "complete", repository, staff)


@router.post("/api/meal-sessions/{number}/actions/skip", response_model=MealSessionResponse)
def skip_session(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cook"})
    return run_staff_action(number, "skip", repository, staff)


@router.post("/api/meal-sessions/{number}/actions/resume", response_model=MealSessionResponse)
def resume_session(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cook"})
    return run_staff_action(number, "resume_after_skip", repository, staff)


@router.post("/api/meal-sessions/{number}/actions/cancel", response_model=MealSessionResponse)
def cancel_session(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    return run_staff_action(number, "cancel", repository, staff)


@router.post("/api/meal-sessions/{number}/actions/mark-unpaid-risk", response_model=MealSessionResponse)
def mark_unpaid_risk(
    number: str,
    repository: MealSessionRepository = Depends(get_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cashier"})
    return run_staff_action(number, "mark_unpaid_risk", repository, staff)


@router.get("/api/stores/{store_id}/queue", response_model=List[MealSessionResponse])
def list_store_queue(store_id: int, repository: MealSessionRepository = Depends(get_repository)):
    return [serialize_session(session) for session in repository.list_active(store_id)]


@router.post(
    "/api/stores/{store_id}/queue/issue",
    response_model=MealSessionResponse,
    status_code=status.HTTP_201_CREATED,
)
def issue_queue_number(
    store_id: int,
    payload: IssueQueueNumberRequest,
    repository: MealSessionRepository = Depends(get_repository),
    catalog_repository: CatalogRepository = Depends(get_catalog_repository),
    operation_logs: OperationLogRepository = Depends(get_operation_log_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    require_store(staff, store_id)
    catalog = catalog_repository.get_catalog(store_id)
    number = repository.next_number(store_id, catalog["store"]["queue_prefix"])
    session = MealSession(
        number=number,
        store_id=store_id,
        people_count=payload.people_count,
        remark=payload.remark,
    )
    saved = repository.save(session)
    operation_logs.record(
        store_id=store_id,
        staff=staff,
        action="queue.issue",
        target_type="meal_session",
        target_id=saved.number,
        detail=payload.remark,
    )
    return serialize_session(saved)


@router.get("/api/stores/{store_id}/cashier/pending", response_model=List[MealSessionResponse])
def list_cashier_pending(store_id: int, repository: MealSessionRepository = Depends(get_repository)):
    return [
        serialize_session(session)
        for session in repository.list_by_status(
            store_id, [QueueStatus.DINING, QueueStatus.CHECKOUT_REQUESTED]
        )
    ]


@router.get("/api/stores/{store_id}/operation-logs", response_model=List[OperationLogResponse])
def list_operation_logs(
    store_id: int,
    repository: OperationLogRepository = Depends(get_operation_log_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    require_store(staff, store_id)
    return repository.list_by_store(store_id)


@router.get("/api/stores/{store_id}/service-calls/pending", response_model=List[ServiceCallResponse])
def list_pending_service_calls(
    store_id: int,
    repository: ServiceCallRepository = Depends(get_service_call_repository),
):
    return repository.list_pending(store_id)


@router.post("/api/service-calls/{call_id}/handle", response_model=ServiceCallResponse)
def handle_service_call(
    call_id: int,
    payload: HandleServiceCallRequest,
    repository: ServiceCallRepository = Depends(get_service_call_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager", "cashier", "cook"})
    try:
        require_store(staff, repository.get_store_id(call_id))
        return repository.handle(call_id, payload.staff_id, payload.resolution)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/stores/{store_id}/catalog")
def store_catalog(store_id: int, repository: CatalogRepository = Depends(get_catalog_repository)):
    return repository.get_catalog(store_id)


@router.patch("/api/stores/{store_id}/business-status")
def update_business_status(
    store_id: int,
    payload: UpdateBusinessStatusRequest,
    repository: CatalogRepository = Depends(get_catalog_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    require_store(staff, store_id)
    try:
        return repository.update_business_status(store_id, payload.business_status)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/api/stores/{store_id}/settings")
def update_store_settings(
    store_id: int,
    payload: UpdateStoreSettingsRequest,
    repository: CatalogRepository = Depends(get_catalog_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    require_store(staff, store_id)
    try:
        return repository.update_store_settings(
            store_id,
            business_hours=payload.business_hours,
            address=payload.address,
            queue_prefix=payload.queue_prefix,
            avg_prepare_minutes=payload.avg_prepare_minutes,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/api/staff/{staff_id}/status")
def update_staff_status(
    staff_id: int,
    payload: UpdateStaffStatusRequest,
    repository: CatalogRepository = Depends(get_catalog_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    try:
        target_store_id = repository.get_staff_store_id(staff_id)
        require_store(staff, target_store_id)
        return repository.update_staff_status(staff_id, payload.status)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.post("/api/stores/{store_id}/dishes", status_code=status.HTTP_201_CREATED)
def create_dish(
    store_id: int,
    payload: CreateDishRequest,
    repository: CatalogRepository = Depends(get_catalog_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    require_store(staff, store_id)
    try:
        return repository.create_dish(
            store_id=store_id,
            name=payload.name,
            category=payload.category,
            price=payload.price,
            available=payload.available,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.patch("/api/dishes/{dish_id}")
def update_dish(
    dish_id: int,
    payload: UpdateDishRequest,
    repository: CatalogRepository = Depends(get_catalog_repository),
    staff: StaffContext = Depends(get_current_staff),
):
    require_roles(staff, {"boss", "manager"})
    try:
        require_store(staff, repository.get_dish_store_id(dish_id))
        return repository.update_dish(
            dish_id=dish_id,
            name=payload.name,
            category=payload.category,
            price=payload.price,
            available=payload.available,
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/api/platform/overview")
def platform_overview():
    return get_platform_overview()


def run_action(number: str, method_name: str, repository: MealSessionRepository):
    session = get_session(number, repository)
    try:
        getattr(session, method_name)()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return serialize_session(repository.save(session))


def run_staff_action(
    number: str,
    method_name: str,
    repository: MealSessionRepository,
    staff: StaffContext,
):
    session = get_session_for_staff(number, staff, repository)
    try:
        getattr(session, method_name)()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    return serialize_session(repository.save(session))


def get_session(number: str, repository: MealSessionRepository) -> MealSession:
    session = repository.get(number)
    if session is None:
        raise HTTPException(status_code=404, detail="meal session not found")
    return session


def get_session_for_staff(number: str, staff: StaffContext, repository: MealSessionRepository) -> MealSession:
    session = repository.get_by_store(staff.store_id, number)
    if session is not None:
        return session
    session = repository.get(number)
    if session is not None:
        require_store(staff, session.store_id)
    else:
        raise HTTPException(status_code=404, detail="meal session not found")
    return session


def serialize_session(session: MealSession) -> MealSessionResponse:
    return MealSessionResponse(
        store_id=session.store_id,
        number=session.number,
        people_count=session.people_count,
        status=session.status.value,
        remark=session.remark,
        total_amount=str(session.total_amount),
        payment_method=session.payment_method or "",
        cashier_id=session.cashier_id or 0,
        items=[
            LineItemResponse(
                name=item.name,
                amount=str(item.amount),
                quantity=item.quantity,
                source=item.source,
                note=item.note,
                subtotal=str(item.subtotal),
            )
            for item in session.items
        ],
    )
