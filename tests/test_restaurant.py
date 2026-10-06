import pytest

from shared.restaurant import (
    EmptyOrder,
    InsufficientPayment,
    InvalidPayment,
    InvalidQuantity,
    ItemNotOrdered,
    RestaurantOrder,
    UnknownMenuItem,
)


def test_orders_are_independent_and_lines_have_subtotals():
    first = RestaurantOrder()
    second = RestaurantOrder()

    first.add(1, 2)
    first.add(4)
    first.add(1)
    second.add(2)

    assert [
        (line.item.number, line.quantity, line.subtotal) for line in first.lines
    ] == [
        (1, 3, 60_000),
        (4, 1, 5_000),
    ]
    assert first.item_count == 4
    assert first.total == 65_000
    assert second.total == 18_000

    first.set_quantity(1, 1)
    first.change_quantity(1, 2)
    first.change_quantity(1, -2)
    first.remove(4)
    assert first.total == 20_000
    assert second.total == 18_000


def test_rejected_changes_leave_the_order_intact():
    order = RestaurantOrder()
    order.add(1)

    with pytest.raises(UnknownMenuItem):
        order.add(99)
    with pytest.raises(UnknownMenuItem):
        order.add(True)
    with pytest.raises(InvalidQuantity):
        order.add(1, 0)
    with pytest.raises(InvalidQuantity):
        order.set_quantity(1, -2)
    with pytest.raises(InvalidQuantity):
        order.change_quantity(1, -1)
    with pytest.raises(ItemNotOrdered):
        order.set_quantity(2, 1)
    with pytest.raises(ItemNotOrdered):
        order.remove(2)
    with pytest.raises(InvalidPayment):
        order.pay(-1)
    with pytest.raises(InvalidPayment):
        order.pay(True)
    with pytest.raises(InsufficientPayment) as exc:
        order.pay(15_000)

    assert exc.value.shortfall == 5_000
    assert order.item_count == 1
    assert order.total == 20_000


def test_payment_returns_receipt_and_clears_only_paid_order():
    order = RestaurantOrder()
    with pytest.raises(EmptyOrder):
        order.pay(20_000)

    order.add(3)
    receipt = order.pay(30_000)
    assert (receipt.total, receipt.paid, receipt.change) == (25_000, 30_000, 5_000)
    assert [(line.item.name, line.quantity) for line in receipt.lines] == [
        ("Ayam Goreng", 1)
    ]
    assert order.lines == ()
    assert order.total == 0

    order.add(4)
    assert order.total == 5_000
    assert receipt.total == 25_000
