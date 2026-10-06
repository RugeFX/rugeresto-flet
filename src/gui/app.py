import flet as ft

from gui.components.layout import restaurant_layout
from gui.components.menu import menu_sections
from gui.components.order_panel import order_panel
from shared.restaurant import (
    EmptyOrder,
    InsufficientPayment,
    InvalidPayment,
    InvalidQuantity,
    ItemNotOrdered,
    MenuItem,
    OrderLine,
    RestaurantError,
    RestaurantOrder,
    UnknownMenuItem,
    rupiah,
)


@ft.component
def RestaurantApp() -> ft.Control:
    restaurant = ft.use_ref(RestaurantOrder)
    _, set_revision = ft.use_state(0)
    payment_draft = ft.use_ref("")
    notice, set_notice = ft.use_state("")
    notice_is_error, set_notice_is_error = ft.use_state(False)
    receipt, set_receipt = ft.use_state(None)

    order = restaurant.current
    lines = order.lines
    total = order.total
    item_count = order.item_count

    def refresh():
        set_revision(lambda revision: revision + 1)

    def report(message: str, is_error: bool = False):
        set_notice(message)
        set_notice_is_error(is_error)

    def error_message(error: RestaurantError) -> str:
        if isinstance(error, UnknownMenuItem):
            return "Menu tidak ditemukan."
        if isinstance(error, ItemNotOrdered):
            return "Menu tersebut belum ada dalam pesanan."
        if isinstance(error, InvalidQuantity):
            return "Jumlah harus berupa angka bulat lebih dari 0."
        if isinstance(error, EmptyOrder):
            return "Tambahkan menu ke pesanan terlebih dahulu."
        if isinstance(error, InvalidPayment):
            return "Nominal pembayaran harus berupa angka bulat tidak negatif."
        if isinstance(error, InsufficientPayment):
            return f"Pembayaran kurang {rupiah(error.shortfall)}."
        return str(error)

    def add_item(item: MenuItem):
        order.add(item.number)
        refresh()
        set_receipt(None)
        report(f"{item.name} ditambahkan ke pesanan.")

    def change_quantity(line: OrderLine, difference: int):
        try:
            order.change_quantity(line.item.number, difference)
        except RestaurantError as error:
            report(error_message(error), True)
            return
        refresh()
        report("")

    def remove_item(item: MenuItem):
        order.remove(item.number)
        if not order.lines:
            payment_draft.current = ""
        refresh()
        report(f"{item.name} dihapus dari pesanan.")

    def finish_payment(amount: int):
        try:
            paid_receipt = order.pay(amount)
        except RestaurantError as error:
            report(error_message(error), True)
            return

        set_receipt(paid_receipt)
        payment_draft.current = ""
        refresh()
        report("")

    def pay(_):
        try:
            amount = int(payment_draft.current)
        except (TypeError, ValueError):
            report("Masukkan nominal pembayaran dalam angka.", True)
            return
        finish_payment(amount)

    def pay_exact(_):
        finish_payment(total)

    def payment_changed(e):
        payment_draft.current = e.control.value

    return restaurant_layout(
        menu_sections(add_item),
        order_panel(
            lines=lines,
            total=total,
            item_count=item_count,
            notice=notice,
            notice_is_error=notice_is_error,
            receipt=receipt,
            on_change=change_quantity,
            on_remove=remove_item,
            payment_changed=payment_changed,
            pay=pay,
            pay_exact=pay_exact,
        ),
    )


def main(page: ft.Page):
    page.title = "RestoRuge · Pesan & bayar"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.render(RestaurantApp)
