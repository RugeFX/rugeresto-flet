import pytest

import shared.restaurant as core
from shared.restaurant import DataFileError, RestaurantSystem


def test_shared_order_roundtrip_and_history(data_dir):
    app = RestaurantSystem(data_dir)
    app.add_order(1, 2)
    app.add_order(4)
    restored = RestaurantSystem(data_dir)
    restored.change_quantity(1, 1)
    restored.remove_item(4)
    assert restored.calculate_total() == 60_000
    receipt = restored.payment(100_000)
    assert (receipt.total, receipt.change) == (60_000, 40_000)
    reopened = RestaurantSystem(data_dir)
    assert reopened.orders == ()
    assert reopened.get_receipt(receipt.order_id) == receipt
    assert app.orders != ()  # Local snapshots need explicit refresh.
    app.refresh()
    assert app.orders == ()
    assert app.get_transactions() == (receipt,)


def test_write_failure_preserves_order(data_dir, monkeypatch):
    app = RestaurantSystem(data_dir)
    app.add_order(1)
    before = (data_dir / "active_order.csv").read_bytes()

    def fail(*_):
        raise PermissionError("denied")

    monkeypatch.setattr(core.os, "replace", fail)
    with pytest.raises(DataFileError):
        app.payment(20_000)
    assert app.calculate_total() == 20_000
    assert app.get_transactions() == ()
    assert (data_dir / "active_order.csv").read_bytes() == before


def test_failed_cleanup_recovery_shared(data_dir, monkeypatch):
    app = RestaurantSystem(data_dir)
    app.add_order(1)
    replace = core.os.replace

    def fail_cleanup(source, dest):
        if dest.name == "active_order.csv":
            raise PermissionError("cleanup denied")
        replace(source, dest)

    with monkeypatch.context() as patch:
        patch.setattr(core.os, "replace", fail_cleanup)
        receipt = app.payment(20_000)
        assert "cleanup is pending" in app.notice
        assert RestaurantSystem(data_dir).orders == ()
    recovered = RestaurantSystem(data_dir)
    assert recovered.get_transactions() == (receipt,)
    assert recovered.orders == ()
