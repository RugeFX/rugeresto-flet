from pathlib import Path

import flet as ft

from gui.components.history import history_view
from gui.components.layout import restaurant_layout
from gui.components.menu import menu_sections
from gui.components.order_panel import order_panel
from shared.restaurant import (
    DATA_DIR,
    MenuItem,
    OrderLine,
    RestaurantError,
    RestaurantSystem,
)


@ft.component
def RestaurantApp(data_dir: Path = DATA_DIR) -> ft.Control:
    restaurant = ft.use_ref(None)
    _, set_revision = ft.use_state(0)
    payment_draft = ft.use_ref("")
    notice, set_notice = ft.use_state("")
    notice_is_error, set_notice_is_error = ft.use_state(False)
    receipt, set_receipt = ft.use_state(None)
    query, set_query = ft.use_state("")
    show_history, set_show_history = ft.use_state(False)
    selected_receipt, set_selected_receipt = ft.use_state(None)

    def redraw():
        set_revision(lambda revision: revision + 1)

    def report(message: str, is_error: bool = False):
        set_notice(message)
        set_notice_is_error(is_error)

    if restaurant.current is None:
        try:
            restaurant.current = RestaurantSystem(data_dir)
        except RestaurantError as error:
            return ft.Container(
                padding=24,
                content=ft.Column(
                    controls=[
                        ft.Text("Data restoran belum dapat dibuka", size=22),
                        ft.Text(str(error), selectable=True),
                        ft.Text("Perbaiki file atau izin akses, lalu coba lagi."),
                        ft.FilledButton(
                            "Coba lagi", key="retry-data", on_click=lambda _: redraw()
                        ),
                    ]
                ),
            )

    system = restaurant.current

    def execute(action, message=""):
        try:
            result = action()
        except RestaurantError as error:
            report(str(error), True)
            redraw()
            return None
        report(system.notice or message)
        redraw()
        return result

    def add_item(item: MenuItem):
        if (
            execute(
                lambda: system.add_order(item.number),
                f"{item.name} ditambahkan ke pesanan.",
            )
            is not None
        ):
            set_receipt(None)

    def change_quantity(line: OrderLine, difference: int):
        execute(lambda: system.change_quantity(line.menu_number, difference))

    def remove_item(line: OrderLine):
        execute(
            lambda: system.remove_item(line.menu_number),
            f"{line.name} dihapus dari pesanan.",
        )
        if not system.orders:
            payment_draft.current = ""

    def finish_payment(amount: int):
        paid = execute(lambda: system.payment(amount))
        if paid is not None:
            set_receipt(paid)
            payment_draft.current = ""

    def pay(_):
        try:
            amount = int(payment_draft.current)
        except (TypeError, ValueError):
            report("Masukkan nominal pembayaran dalam angka.", True)
            return
        finish_payment(amount)

    def refresh(_):
        execute(system.refresh, "Data terbaru dimuat.")
        set_selected_receipt(None)

    def open_history(_):
        refresh(None)
        set_show_history(True)

    tools = ft.Row(
        wrap=True,
        controls=[
            ft.TextButton(
                "Menu", key="show-menu", on_click=lambda _: set_show_history(False)
            ),
            ft.TextButton(
                "Riwayat transaksi", key="show-history", on_click=open_history
            ),
            ft.TextButton("Muat ulang data", key="refresh-data", on_click=refresh),
        ],
    )
    if show_history:
        content = [
            tools,
            *history_view(
                system.get_transactions(), selected_receipt, set_selected_receipt
            ),
        ]
    else:
        items = system.search_menu(query) if query.strip() else system.menu
        content = [
            tools,
            ft.TextField(
                value=None,
                label="Cari menu",
                hint_text="Contoh: nasi goreng",
                key="menu-search",
                on_change=lambda e: set_query(e.control.value or ""),
            ),
        ]
        content.extend(menu_sections(items, add_item, system.menu[0].category))
        if not items:
            content.append(ft.Text("Menu tidak ditemukan. Coba kata lain."))
    return restaurant_layout(
        content,
        order_panel(
            lines=system.orders,
            total=system.calculate_total(),
            item_count=sum(line.quantity for line in system.orders),
            notice=notice or system.notice,
            notice_is_error=notice_is_error,
            receipt=receipt,
            on_change=change_quantity,
            on_remove=remove_item,
            payment_changed=lambda e: setattr(
                payment_draft, "current", e.control.value
            ),
            pay=pay,
            pay_exact=lambda _: finish_payment(system.calculate_total()),
        ),
    )


def main(page: ft.Page):
    page.title = "RestoRuge · Pesan & bayar"
    page.theme_mode = ft.ThemeMode.LIGHT
    page.render(RestaurantApp)
