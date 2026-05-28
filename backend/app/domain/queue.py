from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import List, Optional


class QueueStatus(str, Enum):
    IDLE = "idle"
    OCCUPIED = "occupied"
    PREPARING = "preparing"
    CALLED = "called"
    DINING = "dining"
    CHECKOUT_REQUESTED = "checkout_requested"
    PAID = "paid"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    CANCELLED = "cancelled"
    RISK_UNPAID = "risk_unpaid"


@dataclass
class LineItem:
    name: str
    amount: Decimal
    source: str
    quantity: int = 1
    note: str = ""

    def __post_init__(self):
        if not self.name.strip():
            raise ValueError("line item name is required")
        if self.amount < Decimal("0"):
            raise ValueError("line item amount cannot be negative")
        if self.quantity <= 0:
            raise ValueError("line item quantity must be positive")
        if self.source not in {"staff", "customer", "cashier"}:
            raise ValueError("line item source must be staff, customer, or cashier")

    @property
    def subtotal(self) -> Decimal:
        return self.amount * self.quantity


@dataclass
class MealSession:
    number: str
    store_id: int
    people_count: int
    status: QueueStatus = QueueStatus.OCCUPIED
    items: List[LineItem] = field(default_factory=list)
    remark: str = ""
    cashier_id: Optional[int] = None
    payment_method: Optional[str] = None

    def __post_init__(self):
        if not self.number.strip():
            raise ValueError("queue number is required")
        if self.store_id <= 0:
            raise ValueError("store_id must be positive")
        if self.people_count <= 0:
            raise ValueError("people_count must be positive")

    @property
    def total_amount(self) -> Decimal:
        return sum((item.subtotal for item in self.items), Decimal("0.00"))

    def add_item(self, item: LineItem) -> None:
        if self.status in {QueueStatus.PAID, QueueStatus.COMPLETED, QueueStatus.CANCELLED}:
            raise ValueError("cannot add items to a paid session")
        self.items.append(item)

    def update_remark(self, remark: str) -> None:
        if self.status in {QueueStatus.PAID, QueueStatus.COMPLETED, QueueStatus.CANCELLED}:
            raise ValueError("cannot update a closed session")
        self.remark = remark.strip()

    def append_remark(self, remark: str, source: str) -> None:
        if self.status in {QueueStatus.PAID, QueueStatus.COMPLETED, QueueStatus.CANCELLED}:
            raise ValueError("cannot update a closed session")
        cleaned_remark = remark.strip()
        if not cleaned_remark:
            raise ValueError("remark is required")
        if source not in {"staff", "customer", "cashier"}:
            raise ValueError("remark source must be staff, customer, or cashier")
        entry = f"{source}: {cleaned_remark}"
        self.remark = f"{self.remark}\n{entry}" if self.remark else entry

    def start_preparing(self) -> None:
        self._require_status(QueueStatus.OCCUPIED, "start preparing")
        self.status = QueueStatus.PREPARING

    def call_for_pickup(self) -> None:
        self._require_status(QueueStatus.PREPARING, "call for pickup")
        self.status = QueueStatus.CALLED

    def mark_dining(self) -> None:
        self._require_status(QueueStatus.CALLED, "mark dining")
        self.status = QueueStatus.DINING

    def request_checkout(self) -> None:
        if self.status not in {QueueStatus.OCCUPIED, QueueStatus.PREPARING, QueueStatus.CALLED, QueueStatus.DINING}:
            raise ValueError(f"cannot request checkout from {self.status.value}")
        self.status = QueueStatus.CHECKOUT_REQUESTED

    def confirm_payment(self, payment_method: str, cashier_id: int) -> None:
        if self.status not in {QueueStatus.CHECKOUT_REQUESTED, QueueStatus.DINING}:
            raise ValueError(f"cannot confirm payment from {self.status.value}")
        if not payment_method.strip():
            raise ValueError("payment_method is required")
        if cashier_id <= 0:
            raise ValueError("cashier_id must be positive")
        self.payment_method = payment_method
        self.cashier_id = cashier_id
        self.status = QueueStatus.PAID

    def complete(self) -> None:
        self._require_status(QueueStatus.PAID, "complete")
        self.status = QueueStatus.COMPLETED

    def skip(self) -> None:
        if self.status not in {QueueStatus.OCCUPIED, QueueStatus.PREPARING, QueueStatus.CALLED}:
            raise ValueError(f"cannot skip from {self.status.value}")
        self.status = QueueStatus.SKIPPED

    def resume_after_skip(self) -> None:
        self._require_status(QueueStatus.SKIPPED, "resume after skip")
        self.status = QueueStatus.PREPARING

    def cancel(self) -> None:
        if self.status in {QueueStatus.PAID, QueueStatus.COMPLETED}:
            raise ValueError("cannot cancel a paid session")
        self.status = QueueStatus.CANCELLED

    def mark_unpaid_risk(self) -> None:
        if self.status in {QueueStatus.PAID, QueueStatus.COMPLETED, QueueStatus.CANCELLED}:
            raise ValueError("cannot mark closed session as unpaid risk")
        self.status = QueueStatus.RISK_UNPAID

    def _require_status(self, expected: QueueStatus, action: str) -> None:
        if self.status != expected:
            raise ValueError(
                f"cannot {action} from {self.status.value}; expected {expected.value}"
            )
