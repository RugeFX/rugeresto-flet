from dataclasses import fields, is_dataclass
from types import SimpleNamespace

import flet as ft

from gui.app import RestaurantApp
from shared.restaurant import RestaurantSystem


class GuiHarness:
    """Keep hook state across real component constructions without a Flutter runner."""

    def __init__(self, monkeypatch, data_dir):
        self.slots = []
        self.cursor = 0
        self.data_dir = data_dir
        monkeypatch.setattr(ft, "use_ref", self.use_ref)
        monkeypatch.setattr(ft, "use_state", self.use_state)

    def slot(self, initial):
        index = self.cursor
        self.cursor += 1
        if index == len(self.slots):
            self.slots.append(initial)
        return index

    def use_ref(self, initial):
        return self.slots[self.slot(SimpleNamespace(current=initial))]

    def use_state(self, initial):
        index = self.slot(initial)

        def update(value):
            self.slots[index] = value(self.slots[index]) if callable(value) else value

        return self.slots[index], update

    def render(self):
        self.cursor = 0
        self.root = RestaurantApp.__wrapped__(self.data_dir)
        return self

    def controls(self):
        def walk(value):
            if isinstance(value, ft.Control):
                yield value
                if is_dataclass(value):
                    for field in fields(value):
                        if not field.name.startswith("_"):
                            yield from walk(getattr(value, field.name))
            elif isinstance(value, (list, tuple)):
                for item in value:
                    yield from walk(item)

        return list(walk(self.root))

    def control(self, key):
        return next(control for control in self.controls() if control.key == key)

    def texts(self):
        return "\n".join(
            control.value for control in self.controls() if isinstance(control, ft.Text)
        )


def test_gui_cli_restart_and_history_share_core(data_dir, monkeypatch):
    gui = GuiHarness(monkeypatch, data_dir).render()
    gui.control("add-1").on_click(None)
    gui.render()
    assert RestaurantSystem(data_dir).calculate_total() == 20000
    gui.control("increase-1").on_click(None)
    gui.render()
    assert "2 item dipilih" in gui.texts()
    restored = GuiHarness(monkeypatch, data_dir).render()
    assert "Rp40.000" in restored.texts()
    restored.control("payment-amount").on_change(
        SimpleNamespace(control=SimpleNamespace(value="50000"))
    )
    restored.control("pay").on_click(None)
    restored.render()
    assert "Pembayaran berhasil" in restored.texts()
    assert "Kembalian Rp10.000" in restored.texts()
    core = RestaurantSystem(data_dir)
    receipt = core.get_transactions()[0]
    assert core.orders == ()
    restored.control("show-history").on_click(None)
    restored.render()
    restored.control(f"receipt-{receipt.order_id}").on_click(None)
    restored.render()
    assert "Nasi Goreng ×2" in restored.texts()
    assert receipt.order_id in restored.texts()


def test_gui_search_error_and_retry(data_dir, monkeypatch):
    gui = GuiHarness(monkeypatch, data_dir).render()
    gui.control("menu-search").on_change(
        SimpleNamespace(control=SimpleNamespace(value="  ES   TEH "))
    )
    gui.render()
    assert "Es Teh" in gui.texts()
    assert "Nasi Goreng" not in gui.texts()
    gui.control("add-4").on_click(None)
    gui.render()
    gui.control("payment-amount").on_change(
        SimpleNamespace(control=SimpleNamespace(value="1"))
    )
    gui.control("pay").on_click(None)
    gui.render()
    assert "Insufficient payment" in gui.texts()
    assert RestaurantSystem(data_dir).calculate_total() == 5000
    menu = data_dir / "menu.csv"
    content = menu.read_text()
    menu.unlink()
    broken = GuiHarness(monkeypatch, data_dir).render()
    assert "belum dapat dibuka" in broken.texts()
    menu.write_text(content)
    broken.control("retry-data").on_click(None)
    broken.render()
    assert "Rp5.000" in broken.texts()
