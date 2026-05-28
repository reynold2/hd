from datetime import datetime, timezone
from typing import Dict, List

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import OperationLogModel
from app.repositories.auth import StaffContext


class OperationLogRepository:
    def __init__(self, db: Session):
        self.db = db

    def record(
        self,
        store_id: int,
        staff: StaffContext,
        action: str,
        target_type: str,
        target_id: str,
        detail: str = "",
    ) -> Dict:
        model = OperationLogModel(
            store_id=store_id,
            staff_id=staff.id,
            staff_name=staff.name,
            role=staff.role,
            action=action,
            target_type=target_type,
            target_id=target_id,
            detail=detail,
            created_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        )
        self.db.add(model)
        self.db.commit()
        self.db.refresh(model)
        return self._to_dict(model)

    def list_by_store(self, store_id: int) -> List[Dict]:
        rows = self.db.scalars(
            select(OperationLogModel)
            .where(OperationLogModel.store_id == store_id)
            .order_by(OperationLogModel.id.asc())
        ).all()
        return [self._to_dict(row) for row in rows]

    def _to_dict(self, model: OperationLogModel) -> Dict:
        return {
            "id": model.id,
            "store_id": model.store_id,
            "staff_id": model.staff_id,
            "staff_name": model.staff_name,
            "role": model.role,
            "action": model.action,
            "target_type": model.target_type,
            "target_id": model.target_id,
            "detail": model.detail or "",
            "created_at": model.created_at or "",
        }
