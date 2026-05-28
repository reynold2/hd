from decimal import Decimal
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import LineItemModel, MealSessionModel
from app.domain.queue import LineItem, MealSession, QueueStatus


class MealSessionRepository:
    def __init__(self, db: Session):
        self.db = db

    def save(self, session: MealSession) -> MealSession:
        model = self.db.scalar(select(MealSessionModel).where(MealSessionModel.number == session.number))
        if model is None:
            model = MealSessionModel(number=session.number)
            self.db.add(model)

        model.store_id = session.store_id
        model.people_count = session.people_count
        model.status = session.status.value
        model.remark = session.remark
        model.cashier_id = session.cashier_id or 0
        model.payment_method = session.payment_method or ""
        model.items.clear()
        model.items.extend(
            LineItemModel(
                name=item.name,
                amount=item.amount,
                quantity=item.quantity,
                source=item.source,
                note=item.note,
            )
            for item in session.items
        )
        self.db.commit()
        self.db.refresh(model)
        return self._to_domain(model)

    def get(self, number: str) -> Optional[MealSession]:
        model = self.db.scalar(select(MealSessionModel).where(MealSessionModel.number == number.strip().upper()))
        if model is None:
            return None
        return self._to_domain(model)

    def list_active(self, store_id: int) -> List[MealSession]:
        rows = self.db.scalars(
            select(MealSessionModel)
            .where(MealSessionModel.store_id == store_id)
            .where(MealSessionModel.status.notin_(["completed", "cancelled"]))
            .order_by(MealSessionModel.id.asc())
        ).all()
        return [self._to_domain(row) for row in rows]

    def list_by_status(self, store_id: int, statuses: List[QueueStatus]) -> List[MealSession]:
        rows = self.db.scalars(
            select(MealSessionModel)
            .where(MealSessionModel.store_id == store_id)
            .where(MealSessionModel.status.in_([status.value for status in statuses]))
            .order_by(MealSessionModel.id.asc())
        ).all()
        return [self._to_domain(row) for row in rows]

    def next_number(self, store_id: int, prefix: str = "A") -> str:
        rows = self.db.scalars(
            select(MealSessionModel.number)
            .where(MealSessionModel.store_id == store_id)
            .where(MealSessionModel.number.like(f"{prefix}%"))
        ).all()
        max_index = 0
        for number in rows:
            suffix = number.replace(prefix, "", 1)
            if suffix.isdigit():
                max_index = max(max_index, int(suffix))
        return f"{prefix}{max_index + 1:03d}"

    def _to_domain(self, model: MealSessionModel) -> MealSession:
        session = MealSession(
            number=model.number,
            store_id=model.store_id,
            people_count=model.people_count,
            status=QueueStatus(model.status),
            remark=model.remark or "",
            cashier_id=model.cashier_id or None,
            payment_method=model.payment_method or None,
        )
        session.items = [
            LineItem(
                name=item.name,
                amount=Decimal(item.amount).quantize(Decimal("0.01")),
                quantity=item.quantity,
                source=item.source,
                note=item.note or "",
            )
            for item in model.items
        ]
        return session
