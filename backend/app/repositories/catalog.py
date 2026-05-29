from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import DishModel, StaffModel, StoreModel


class CatalogRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_catalog(self, store_id: int) -> Dict:
        store = self._get_or_seed_store(store_id)
        return {
            "store": self._store_payload(store),
            "dishes": [self._dish_payload(dish) for dish in store.dishes],
            "staff": [self._staff_payload(staff) for staff in store.staff],
            "queue_rules": {
                "allow_customer_add_items": True,
                "allow_checkout_request": True,
                "max_active_sessions_per_customer": 1,
                "estimate_minutes_per_order": 5,
            },
        }

    def update_business_status(self, store_id: int, business_status: str) -> Dict:
        if business_status not in {"open", "paused", "closed"}:
            raise ValueError("business_status must be open, paused, or closed")
        store = self._get_or_seed_store(store_id)
        store.business_status = business_status
        self.db.commit()
        self.db.refresh(store)
        return self._store_payload(store)

    def update_store_settings(
        self,
        store_id: int,
        business_hours: Optional[str] = None,
        address: Optional[str] = None,
        queue_prefix: Optional[str] = None,
        avg_prepare_minutes: Optional[int] = None,
    ) -> Dict:
        store = self._get_or_seed_store(store_id)
        if business_hours is not None:
            store.business_hours = business_hours.strip() or store.business_hours
        if address is not None:
            store.address = address.strip() or store.address
        if queue_prefix is not None:
            prefix = queue_prefix.strip().upper()
            if not prefix:
                raise ValueError("queue_prefix is required")
            store.queue_prefix = prefix
        if avg_prepare_minutes is not None:
            if avg_prepare_minutes <= 0:
                raise ValueError("avg_prepare_minutes must be positive")
            store.avg_prepare_minutes = avg_prepare_minutes
        self.db.commit()
        self.db.refresh(store)
        return self._store_payload(store)

    def update_staff_status(self, staff_id: int, status: str) -> Dict:
        staff = self.db.get(StaffModel, staff_id)
        if staff is None:
            raise KeyError("staff not found")
        if status not in {"active", "inactive"}:
            raise ValueError("status must be active or inactive")
        staff.status = status
        self.db.commit()
        self.db.refresh(staff)
        return self._staff_payload(staff)

    def get_staff_store_id(self, staff_id: int) -> int:
        staff = self.db.get(StaffModel, staff_id)
        if staff is None:
            raise KeyError("staff not found")
        return staff.store_id

    def create_dish(self, store_id: int, name: str, category: str, price: Decimal, available: bool) -> Dict:
        store = self._get_or_seed_store(store_id)
        dish = DishModel(
            store_id=store.id,
            name=name.strip(),
            category=category.strip() or "推荐",
            price=price,
            available=1 if available else 0,
        )
        if not dish.name:
            raise ValueError("dish name is required")
        if price < Decimal("0"):
            raise ValueError("dish price cannot be negative")
        self.db.add(dish)
        self.db.commit()
        self.db.refresh(dish)
        return self._dish_payload(dish)

    def update_dish(
        self,
        dish_id: int,
        name: Optional[str] = None,
        category: Optional[str] = None,
        price: Optional[Decimal] = None,
        available: Optional[bool] = None,
    ) -> Dict:
        dish = self.db.get(DishModel, dish_id)
        if dish is None:
            raise KeyError("dish not found")
        if name is not None:
            if not name.strip():
                raise ValueError("dish name is required")
            dish.name = name.strip()
        if category is not None:
            dish.category = category.strip() or "推荐"
        if price is not None:
            if price < Decimal("0"):
                raise ValueError("dish price cannot be negative")
            dish.price = price
        if available is not None:
            dish.available = 1 if available else 0
        self.db.commit()
        self.db.refresh(dish)
        return self._dish_payload(dish)

    def get_dish_store_id(self, dish_id: int) -> int:
        dish = self.db.get(DishModel, dish_id)
        if dish is None:
            raise KeyError("dish not found")
        return dish.store_id

    def _get_or_seed_store(self, store_id: int) -> StoreModel:
        store = self.db.get(StoreModel, store_id)
        if store is not None:
            return store

        store = StoreModel(
            id=store_id,
            merchant_id=1,
            name="川香麻辣烫（中山店）",
            business_status="open",
            business_hours="10:00-22:30",
            phone="0760-12345678",
            address="中山市东区中山三路88号",
            queue_prefix="A",
            avg_prepare_minutes=18,
        )
        self.db.add(store)
        self.db.flush()
        self.db.add_all(
            [
                DishModel(store_id=store.id, name="招牌麻辣烫", category="推荐", price=Decimal("12.00")),
                DishModel(store_id=store.id, name="牛肉串", category="荤菜", price=Decimal("15.00")),
                DishModel(store_id=store.id, name="宽粉", category="主食", price=Decimal("2.00")),
                DishModel(store_id=store.id, name="金针菇", category="素菜", price=Decimal("3.00")),
                DishModel(store_id=store.id, name="冰粉", category="饮品", price=Decimal("6.00")),
            ]
        )
        self.db.add_all(
            [
                StaffModel(store_id=store.id, name="张老板", role="boss"),
                StaffModel(store_id=store.id, name="李店长", role="manager"),
                StaffModel(store_id=store.id, name="王收银", role="cashier"),
                StaffModel(store_id=store.id, name="赵师傅", role="cook"),
            ]
        )
        self.db.commit()
        return self.db.scalar(select(StoreModel).where(StoreModel.id == store_id))

    def _store_payload(self, store: StoreModel) -> Dict:
        return {
            "id": store.id,
            "merchant_id": store.merchant_id,
            "name": store.name,
            "business_status": store.business_status,
            "business_hours": store.business_hours,
            "phone": store.phone,
            "address": store.address,
            "queue_prefix": store.queue_prefix,
            "avg_prepare_minutes": store.avg_prepare_minutes,
        }

    def _dish_payload(self, dish: DishModel) -> Dict:
        return {
            "id": dish.id,
            "name": dish.name,
            "category": dish.category,
            "price": str(Decimal(dish.price).quantize(Decimal("0.01"))),
            "available": bool(dish.available),
        }

    def _staff_payload(self, staff: StaffModel) -> Dict:
        return {"id": staff.id, "name": staff.name, "role": staff.role, "status": staff.status}
