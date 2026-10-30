import csv
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

import base
from base import (
    DATA_DIR,
    ORDER_FIELDS,
    TRANSACTION_FIELDS,
    DataFileError,
    RestaurantError,
    RestaurantSystem,
    run_cli,
)


@pytest.fixture
def data_dir(tmp_path):
    shutil.copy(DATA_DIR / "menu.csv", tmp_path / "menu.csv")
    for name, fields in (
        ("active_order.csv", ORDER_FIELDS),
        ("transactions.csv", TRANSACTION_FIELDS),
    ):
        (tmp_path / name).write_text(",".join(fields) + "\n", encoding="utf-8")
    return tmp_path


def rows(path):
    with path.open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def test_catalog_and_normalized_search(data_dir):
    app = RestaurantSystem(data_dir)
    assert [(item.number, item.price) for item in app.menu] == [
        (1, 20_000),
        (2, 18_000),
        (3, 25_000),
        (4, 5_000),
        (5, 8_000),
    ]
    assert [item.name for item in app.search_menu("  NASI   GORENG \t")] == [
        "Nasi Goreng"
    ]
    assert len(app.search_menu("goreng")) == 3
    assert app.search_menu("pizza") == ()
    with pytest.raises(RestaurantError, match="Enter a menu name"):
        app.search_menu("  ")


def test_order_changes_are_durable(data_dir):
    app = RestaurantSystem(data_dir)
    app.add_order(1, 2)
    app.add_order(1, 1)
    app.add_order(4, 2)
    restored = RestaurantSystem(data_dir)
    assert [line.quantity for line in restored.orders] == [3, 2]
    assert restored.calculate_total() == 70_000
    restored.update_order(1, 1)
    assert RestaurantSystem(data_dir).calculate_total() == 30_000
    assert restored.delete_order(2).name == "Es Teh"
    assert RestaurantSystem(data_dir).calculate_total() == 20_000
    restored.delete_order(1)
    assert RestaurantSystem(data_dir).orders == ()
    assert rows(data_dir / "active_order.csv") == []


def test_rejected_operations_do_not_change_saved_order(data_dir):
    app = RestaurantSystem(data_dir)
    app.add_order(1, 1)
    saved = (data_dir / "active_order.csv").read_bytes()
    for action in (
        lambda: app.add_order(99, 1),
        lambda: app.add_order(True, 1),
        lambda: app.add_order(1, 0),
        lambda: app.add_order(1, 1.5),
        lambda: app.update_order(1, -1),
        lambda: app.update_order(2, 1),
        lambda: app.delete_order(99),
        lambda: app.payment(-1),
        lambda: app.payment(True),
        lambda: app.payment(19_999),
    ):
        with pytest.raises(RestaurantError):
            action()
        assert app.calculate_total() == 20_000
        assert (data_dir / "active_order.csv").read_bytes() == saved
        assert rows(data_dir / "transactions.csv") == []


def test_payment_history_and_snapshots_survive_restart(data_dir):
    app = RestaurantSystem(data_dir)
    with pytest.raises(RestaurantError, match="empty"):
        app.payment(10_000)
    app.add_order(1, 2)
    app.add_order(4, 1)
    receipt = app.payment(50_000)
    assert (receipt.total, receipt.paid, receipt.change) == (45_000, 50_000, 5_000)
    assert app.orders == ()
    restored = RestaurantSystem(data_dir)
    assert restored.get_receipt(f"  {receipt.order_id.upper()}  ") == receipt
    assert len(restored.get_transactions()) == 1  # Two item rows, one payment.
    with pytest.raises(RestaurantError, match="Receipt not found"):
        restored.get_receipt("unknown")
    path = data_dir / "menu.csv"
    path.write_text(path.read_text().replace("Nasi Goreng,20000", "Nasi Baru,30000"))
    changed = RestaurantSystem(data_dir)
    assert changed.get_transactions()[0].lines[0].unit_price == 20_000
    assert changed.get_transactions()[0].lines[0].name == "Nasi Goreng"
    changed.add_order(1, 1)
    assert changed.calculate_total() == 30_000
    changed.payment(30_000)
    assert len(RestaurantSystem(data_dir).get_transactions()) == 2


@pytest.mark.parametrize("operation", ["add", "update", "delete", "pay"])
def test_failed_write_retains_memory_and_file(data_dir, monkeypatch, operation):
    app = RestaurantSystem(data_dir)
    app.add_order(1, 2)
    before = {p.name: p.read_bytes() for p in data_dir.glob("*.csv")}
    original_orders = app.orders

    def fail_replace(*_):
        raise PermissionError("simulated write denial")

    monkeypatch.setattr(base.os, "replace", fail_replace)
    actions = {
        "add": lambda: app.add_order(4, 1),
        "update": lambda: app.update_order(1, 3),
        "delete": lambda: app.delete_order(1),
        "pay": lambda: app.payment(50_000),
    }
    with pytest.raises(DataFileError, match="Cannot save"):
        actions[operation]()
    assert app.orders == original_orders
    assert app.get_transactions() == ()
    assert {p.name: p.read_bytes() for p in data_dir.glob("*.csv")} == before
    assert not list(data_dir.glob("*.tmp"))


def test_paid_order_cleanup_failure_cannot_duplicate_payment(data_dir, monkeypatch):
    app = RestaurantSystem(data_dir)
    app.add_order(1, 1)
    original_replace = base.os.replace

    def fail_order_cleanup(source, destination):
        if Path(destination).name == "active_order.csv":
            raise PermissionError("simulated cleanup denial")
        original_replace(source, destination)

    with monkeypatch.context() as patch:
        patch.setattr(base.os, "replace", fail_order_cleanup)
        receipt = app.payment(25_000)
        assert app.orders == ()
        assert "cleanup is pending" in app.notice
        with pytest.raises(RestaurantError, match="empty"):
            app.payment(25_000)
        restarted = RestaurantSystem(data_dir)
        assert restarted.orders == ()
        assert restarted.get_transactions() == (receipt,)
        assert "will not be charged again" in restarted.notice
    recovered = RestaurantSystem(data_dir)
    assert recovered.orders == ()
    assert rows(data_dir / "active_order.csv") == []
    recovered.add_order(4, 1)
    recovered.payment(5_000)
    assert len(RestaurantSystem(data_dir).get_transactions()) == 2


def test_conflicting_paid_and_active_data_is_not_discarded(data_dir):
    app = RestaurantSystem(data_dir)
    app.add_order(1, 1)
    active = (data_dir / "active_order.csv").read_text()
    app.payment(20_000)
    path = data_dir / "active_order.csv"
    path.write_text(active.replace(",20000,1", ",20000,2"))
    saved = path.read_bytes()
    with pytest.raises(DataFileError, match="conflicts"):
        RestaurantSystem(data_dir)
    assert path.read_bytes() == saved


@pytest.mark.parametrize(
    "filename,content",
    [
        ("menu.csv", "wrong,header\n"),
        ("menu.csv", "number,name,price,category,detail\n1,Nasi,bad,Food,Meal\n"),
        (
            "menu.csv",
            "number,name,price,category,detail\n1,Nasi,1,Food,Meal\n1,Mie,2,Food,Meal\n",
        ),
        ("menu.csv", "number,name,price,category,detail\n"),
        ("menu.csv", 'number,name,price,category,detail\n1,"unclosed,1,Food,Meal\n'),
        (
            "active_order.csv",
            "order_id,menu_number,name,unit_price,quantity\nx,1,Nasi,20000,0\n",
        ),
        (
            "active_order.csv",
            "order_id,menu_number,name,unit_price,quantity\nx,1,Nasi,20000,1\ny,4,Teh,5000,1\n",
        ),
    ],
)
def test_invalid_data_is_rejected_without_repair(data_dir, filename, content):
    path = data_dir / filename
    path.write_text(content)
    before = path.read_bytes()
    with pytest.raises(DataFileError):
        RestaurantSystem(data_dir)
    assert path.read_bytes() == before


@pytest.mark.parametrize(
    "column,value",
    [
        ("line_total", "1"),
        ("order_total", "1"),
        ("paid", "0"),
        ("change", "1"),
        ("paid_at", "2026-10-30T12:00:00"),
    ],
)
def test_corrupt_transaction_is_rejected(data_dir, column, value):
    app = RestaurantSystem(data_dir)
    app.add_order(1, 1)
    app.payment(20_000)
    path = data_dir / "transactions.csv"
    records = rows(path)
    records[0][column] = value
    with path.open("w", newline="") as file:
        writer = csv.DictWriter(file, TRANSACTION_FIELDS)
        writer.writeheader()
        writer.writerows(records)
    before = path.read_bytes()
    with pytest.raises(DataFileError):
        RestaurantSystem(data_dir)
    assert path.read_bytes() == before


def test_missing_file_has_actionable_error(data_dir):
    (data_dir / "menu.csv").unlink()
    with pytest.raises(DataFileError, match="menu.csv"):
        RestaurantSystem(data_dir)


def test_csv_handles_comma_in_menu_name(data_dir):
    path = data_dir / "menu.csv"
    path.write_text(path.read_text().replace("Nasi Goreng,", '"Nasi, Goreng",'))
    app = RestaurantSystem(data_dir)
    app.add_order(1, 1)
    assert RestaurantSystem(data_dir).orders[0].name == "Nasi, Goreng"
    app.payment(20_000)
    assert (
        RestaurantSystem(data_dir).get_transactions()[0].lines[0].name == "Nasi, Goreng"
    )


def test_cli_rejects_invalid_inputs_and_keeps_running(data_dir):
    answers = iter(
        [
            "bad",
            "7",
            "  NASI   GORENG  ",
            "7",
            " ",
            "2",
            "abc",
            "2",
            "1",
            "0",
            "2",
            "1",
            "1",
            "6",
            "",
            "6",
            "10000",
            "6",
            "30000",
            "8",
            " Q ",
        ]
    )
    output = []
    run_cli(
        RestaurantSystem(data_dir), read=lambda _: next(answers), write=output.append
    )
    text = "\n".join(output)
    assert "1. Nasi Goreng - Rp20,000" in text
    assert "Enter a menu name" in text
    assert "greater than 0" in text
    assert "whole number without currency" in text
    assert "still need Rp10,000" in text
    assert "Change  : Rp10,000" in text
    assert "Transactions: 1 | Sales: Rp20,000" in text
    assert output[-1] == "Program closed."


def test_actual_program_restores_order_from_another_working_directory(data_dir):
    script = Path(base.__file__)

    def run(answers):
        return subprocess.run(
            [sys.executable, str(script), "--data-dir", str(data_dir)],
            input="\n".join(answers) + "\n",
            text=True,
            capture_output=True,
            cwd=data_dir,
            check=True,
        ).stdout

    assert "added to order" in run(["2", "1", "2", "10"])
    paid = run(["3", "6", "50000", "10"])
    assert "Restored 1 saved order line" in paid
    assert "Nasi Goreng x2 - Rp40,000" in paid
    assert "Change  : Rp10,000" in paid
    history = run(["3", "8", "q"])
    assert "Your order is empty" in history
    assert "Transactions: 1 | Sales: Rp40,000" in history


def test_program_can_retry_missing_data_and_exit_without_traceback(tmp_path):
    result = subprocess.run(
        [sys.executable, base.__file__, "--data-dir", str(tmp_path)],
        input="retry\nq\n",
        text=True,
        capture_output=True,
        cwd=tmp_path,
        check=False,
    )
    assert result.returncode == 1
    assert result.stdout.count("Cannot read") == 2
    assert "menu.csv" in result.stdout
    assert result.stderr == ""
    assert list(tmp_path.iterdir()) == []
