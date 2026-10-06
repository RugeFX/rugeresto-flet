from collections.abc import Callable

import flet as ft

from gui.components.order_row import order_row
from gui.theme import Color
from shared.restaurant import MenuItem, OrderLine, Receipt, rupiah


def order_panel(
    *,
    lines: tuple[OrderLine, ...],
    total: int,
    item_count: int,
    notice: str,
    notice_is_error: bool,
    receipt: Receipt | None,
    on_change: Callable[[OrderLine, int], None],
    on_remove: Callable[[MenuItem], None],
    payment_changed: Callable,
    pay: Callable,
    pay_exact: Callable,
) -> ft.Container:
    if lines:
        order_content = ft.Column(
            spacing=0,
            controls=[order_row(line, on_change, on_remove) for line in lines],
        )
    else:
        order_content = ft.Container(
            padding=ft.Padding.symmetric(vertical=28, horizontal=18),
            alignment=ft.Alignment.CENTER,
            bgcolor=Color.background,
            border_radius=10,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=8,
                controls=[
                    ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, size=30, color=Color.green),
                    ft.Text(
                        "Pesanan masih kosong",
                        weight=ft.FontWeight.BOLD,
                        color=Color.ink,
                    ),
                    ft.Text(
                        "Pilih hidangan di menu untuk memulai.",
                        size=12,
                        color=Color.muted,
                        text_align=ft.TextAlign.CENTER,
                    ),
                ],
            ),
        )

    feedback = None
    if notice:
        feedback = ft.Container(
            padding=ft.Padding.symmetric(vertical=11, horizontal=13),
            bgcolor=Color.danger_light if notice_is_error else Color.green_light,
            border_radius=8,
            content=ft.Text(
                notice,
                size=12,
                color=Color.danger if notice_is_error else Color.green_dark,
            ),
        )

    receipt_card = None
    if receipt:
        receipt_card = ft.Container(
            padding=16,
            bgcolor=Color.green_light,
            border_radius=10,
            content=ft.Column(
                spacing=5,
                controls=[
                    ft.Row(
                        spacing=7,
                        controls=[
                            ft.Icon(
                                ft.Icons.CHECK_CIRCLE_ROUNDED,
                                color=Color.green,
                                size=19,
                            ),
                            ft.Text(
                                "Pembayaran berhasil",
                                color=Color.green_dark,
                                weight=ft.FontWeight.BOLD,
                            ),
                        ],
                    ),
                    ft.Text(
                        f"Total {rupiah(receipt.total)} · Dibayar {rupiah(receipt.paid)}",
                        size=12,
                        color=Color.muted,
                    ),
                    ft.Text(
                        f"Kembalian {rupiah(receipt.change)}",
                        weight=ft.FontWeight.BOLD,
                        color=Color.green_dark,
                    ),
                    ft.Text(
                        "Pilih menu untuk membuat pesanan baru.",
                        size=12,
                        color=Color.muted,
                    ),
                ],
            ),
        )

    order_panel = ft.Container(
        col={"xs": 12, "lg": 4},
        padding=20,
        bgcolor=Color.surface,
        border=ft.Border.all(1, Color.line),
        border_radius=14,
        content=ft.Column(
            spacing=16,
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(
                                    "Pesananmu",
                                    size=20,
                                    weight=ft.FontWeight.BOLD,
                                    color=Color.ink,
                                ),
                                ft.Text(
                                    f"{item_count} item dipilih",
                                    size=12,
                                    color=Color.muted,
                                ),
                            ],
                        ),
                        ft.Icon(ft.Icons.RECEIPT_LONG_OUTLINED, color=Color.green),
                    ],
                ),
                *([receipt_card] if receipt_card else []),
                order_content,
                ft.Container(
                    padding=ft.Padding.only(top=3),
                    content=ft.Row(
                        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                        controls=[
                            ft.Text("Total pembayaran", color=Color.muted),
                            ft.Text(
                                rupiah(total),
                                size=22,
                                weight=ft.FontWeight.BOLD,
                                color=Color.ink,
                            ),
                        ],
                    ),
                ),
                *(
                    [
                        ft.TextField(
                            value=None,
                            label="Uang diterima",
                            hint_text="Masukkan nominal",
                            prefix=ft.Text("Rp "),
                            keyboard_type=ft.KeyboardType.NUMBER,
                            on_change=payment_changed,
                            on_submit=pay,
                            key="payment-amount",
                        ),
                        ft.TextButton(
                            f"Bayar pas {rupiah(total)}",
                            on_click=pay_exact,
                            key="exact-payment",
                        ),
                        ft.FilledButton(
                            "Bayar sekarang",
                            icon=ft.Icons.PAYMENTS_OUTLINED,
                            bgcolor=Color.green,
                            color=Color.surface,
                            height=48,
                            on_click=pay,
                            key="pay",
                        ),
                    ]
                    if lines
                    else []
                ),
                *([feedback] if feedback else []),
            ],
        ),
    )

    return order_panel
