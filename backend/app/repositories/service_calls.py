from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import ServiceCallModel


class ServiceCallRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, store_id: int, number: str, message: str, source: str) -> Dict:
        cleaned_message = message.strip()
        if not cleaned_message:
            raise ValueError("service call message is required")
        if source not in {"staff", "customer", "cashier"}:
            raise ValueError("service call source must be staff, customer, or cashier")

        model = ServiceCallModel(
            store_id=store_id,
            number=number.strip().upper(),
            message=cleaned_message,
            source=source,
            status="pending",
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_dict(model)

    def list_pending(self, store_id: int) -> List[Dict]:
        rows = self.db.scalars(
            select(ServiceCallModel)
            .where(ServiceCallModel.store_id == store_id)
            .where(ServiceCallModel.status == "pending")
            .order_by(ServiceCallModel.id.asc())
        ).all()
        return [self._to_dict(row) for row in rows]

    def get_store_id(self, call_id: int) -> int:
        model = self.db.get(ServiceCallModel, call_id)
        if model is None:
            raise KeyError("service call not found")
        return model.store_id

    def handle(self, call_id: int, staff_id: int, resolution: str) -> Dict:
        if staff_id <= 0:
            raise ValueError("staff_id must be positive")
        model = self.db.get(ServiceCallModel, call_id)
        if model is None:
            raise KeyError("service call not found")
        model.status = "handled"
        model.handled_by = staff_id
        model.resolution = resolution.strip()
        self.db.commit()
        self.db.refresh(model)
        return self._to_dict(model)

    def get_store_id(self, call_id: int) -> int:
        model = self.db.get(ServiceCallModel, call_id)
        if model is None:
            raise KeyError("service call not found")
        return model.store_id

    def _to_dict(self, model: ServiceCallModel) -> Dict:
        return {
            "id": model.id,
            "store_id": model.store_id,
            "number": model.number,
            "message": model.message,
            "source": model.source,
            "status": model.status,
            "handled_by": model.handled_by or 0,
            "resolution": model.resolution or "",
        }
