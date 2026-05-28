from decimal import Decimal

import pytest

from app.domain.queue import LineItem, MealSession, QueueStatus


def test_meal_session_completes_after_cashier_confirms_payment():
    session = MealSession(number="A018", store_id=1, people_count=2)

    session.add_item(LineItem(name="称重菜篮", amount=Decimal("26.00"), source="staff"))
    session.add_item(LineItem(name="冰粉", amount=Decimal("6.00"), source="customer"))
    session.start_preparing()
    session.call_for_pickup()
    session.mark_dining()
    session.request_checkout()
    session.confirm_payment(payment_method="store_qr", cashier_id=9)
    session.complete()

    assert session.status == QueueStatus.COMPLETED
    assert session.total_amount == Decimal("32.00")
    assert session.cashier_id == 9
    assert session.payment_method == "store_qr"


def test_customer_can_add_items_until_payment_is_confirmed():
    session = MealSession(number="A019", store_id=1, people_count=1)
    session.add_item(LineItem(name="牛肉串", amount=Decimal("15.00"), source="staff"))
    session.request_checkout()

    session.add_item(LineItem(name="可乐", amount=Decimal("5.00"), source="customer"))
    session.confirm_payment(payment_method="store_qr", cashier_id=3)

    with pytest.raises(ValueError, match="paid session"):
        session.add_item(LineItem(name="午餐肉", amount=Decimal("8.00"), source="customer"))

    assert session.total_amount == Decimal("20.00")


def test_customer_remark_is_appended_without_losing_existing_remark():
    session = MealSession(number="A023", store_id=1, people_count=1, remark="少辣")

    session.append_remark("加麻加汤", source="customer")

    assert session.remark == "少辣\ncustomer: 加麻加汤"


def test_closed_session_cannot_append_remark():
    session = MealSession(number="A024", store_id=1, people_count=1)
    session.request_checkout()
    session.confirm_payment(payment_method="store_qr", cashier_id=3)

    with pytest.raises(ValueError, match="cannot update a closed session"):
        session.append_remark("已离店", source="customer")


def test_invalid_state_transition_is_rejected():
    session = MealSession(number="A020", store_id=1, people_count=3)

    with pytest.raises(ValueError, match="occupied"):
        session.call_for_pickup()

    assert session.status == QueueStatus.OCCUPIED


def test_called_session_can_be_skipped_and_resumed_for_preparation():
    session = MealSession(number="A021", store_id=1, people_count=2)
    session.start_preparing()
    session.call_for_pickup()

    session.skip()
    assert session.status == QueueStatus.SKIPPED

    session.resume_after_skip()
    assert session.status == QueueStatus.PREPARING


def test_paid_session_cannot_be_cancelled_or_marked_as_unpaid_risk():
    session = MealSession(number="A022", store_id=1, people_count=2)
    session.request_checkout()
    session.confirm_payment(payment_method="store_qr", cashier_id=3)

    with pytest.raises(ValueError, match="cannot cancel a paid session"):
        session.cancel()

    with pytest.raises(ValueError, match="cannot mark closed session"):
        session.mark_unpaid_risk()

    assert session.status == QueueStatus.PAID
