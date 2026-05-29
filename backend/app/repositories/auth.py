import base64
import hashlib
import hmac
from dataclasses import dataclass
from typing import Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import RoleBindingModel, StaffModel
from app.repositories.catalog import CatalogRepository


TOKEN_SECRET = "queue-calling-dev-secret"

ROLE_ENTRY_PAGES = {
    "customer": "/pages/detail/detail",
    "boss": "/pages/boss/index",
    "staff": "/pages/staff/index",
    "kitchen": "/pages/kitchen/index",
    "cashier": "/pages/cashier/index",
}


@dataclass(frozen=True)
class StaffContext:
    id: int
    store_id: int
    name: str
    role: str
    status: str


class AuthRepository:
    def __init__(self, db: Session):
        self.db = db

    def login(self, store_id: int, staff_name: str, pin: str) -> dict:
        if pin != "0000":
            raise ValueError("invalid staff credentials")
        staff = self._find_staff(store_id, staff_name)
        if staff is None or staff.status != "active":
            raise ValueError("invalid staff credentials")
        context = self._to_context(staff)
        return {"token": self.issue_token(context), "staff": self._context_payload(context)}

    def resolve_wechat_role(self, openid: str, store_id: int) -> dict:
        CatalogRepository(self.db).get_catalog(store_id)
        binding = self.db.scalar(
            select(RoleBindingModel)
            .where(RoleBindingModel.openid == openid.strip())
            .where(RoleBindingModel.store_id == store_id)
        )
        if binding is None or not binding.enabled:
            raise ValueError("openid is not bound to this store")
        catalog = CatalogRepository(self.db).get_catalog(store_id)
        return self._role_binding_payload(binding, catalog["store"])

    def wechat_login(self, openid: str, store_id: int) -> dict:
        return self.resolve_wechat_role(openid, store_id)

    def issue_token(self, staff: StaffContext) -> str:
        payload = f"{staff.id}:{staff.store_id}:{staff.role}"
        encoded_payload = base64.urlsafe_b64encode(payload.encode("utf-8")).decode("ascii").rstrip("=")
        signature = hmac.new(TOKEN_SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256)
        return f"{encoded_payload}.{signature.hexdigest()}"

    def verify_token(self, token: str) -> StaffContext:
        try:
            encoded_payload, signature = token.split(".", 1)
        except ValueError:
            raise ValueError("invalid token")
        expected_signature = hmac.new(
            TOKEN_SECRET.encode("utf-8"), encoded_payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("invalid token")
        payload = base64.urlsafe_b64decode(encoded_payload + "=" * (-len(encoded_payload) % 4)).decode("utf-8")
        staff_id, store_id, role = payload.split(":", 2)
        staff = self.db.get(StaffModel, int(staff_id))
        if staff is None or staff.status != "active":
            raise ValueError("invalid token")
        if staff.store_id != int(store_id) or staff.role != role:
            raise ValueError("invalid token")
        return self._to_context(staff)

    def _find_staff(self, store_id: int, staff_name: str) -> Optional[StaffModel]:
        CatalogRepository(self.db).get_catalog(store_id)
        return self.db.scalar(
            select(StaffModel)
            .where(StaffModel.store_id == store_id)
            .where(StaffModel.name == staff_name.strip())
        )

    def _to_context(self, staff: StaffModel) -> StaffContext:
        return StaffContext(
            id=staff.id,
            store_id=staff.store_id,
            name=staff.name,
            role=staff.role,
            status=staff.status,
        )

    def _context_payload(self, staff: StaffContext) -> dict:
        return {
            "id": staff.id,
            "store_id": staff.store_id,
            "name": staff.name,
            "role": staff.role,
            "status": staff.status,
        }

    def _role_binding_payload(self, binding: RoleBindingModel, store: dict) -> dict:
        return {
            "user_id": binding.user_id,
            "display_name": binding.display_name,
            "openid": binding.openid,
            "role": binding.role,
            "store_id": binding.store_id,
            "store": store,
            "entry_page": ROLE_ENTRY_PAGES.get(binding.role, "/pages/index/index"),
        }
