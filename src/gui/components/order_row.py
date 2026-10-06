from collections.abc import Callable

import flet as ft

from gui.theme import Color
from shared.restaurant import MenuItem, OrderLine, rupiah


def order_row(
    line: OrderLine,
    on_change: Callable[[OrderLine, int], None],
    on_remove: Callable[[MenuItem], None],
) -> ft.Container:
    item = line.item
    quantity = line.quantity
    return ft.Container(
        padding=ft.Padding.symmetric(vertical=13),
        border=ft.Border.only(bottom=ft.BorderSide(1, Color.line)),
        content=ft.Column(
            spacing=9,
            controls=[
                ft.Row(
                    controls=[
                        ft.Column(
                            expand=True,
                            spacing=2,
                            controls=[
                                ft.Text(
                                    item.name,
                                    weight=ft.FontWeight.BOLD,
                                    color=Color.ink,
                                ),
                                ft.Text(
                                    f"{rupiah(item.price)} / porsi",
                                    size=12,
                                    color=Color.muted,
                                ),
                            ],
                        ),
                        ft.Text(
                            rupiah(line.subtotal),
                            weight=ft.FontWeight.BOLD,
                            color=Color.ink,
                        ),
                    ],
                ),
                ft.Row(
                    spacing=3,
                    controls=[
                        ft.IconButton(
                            icon=ft.Icons.REMOVE,
                            icon_size=17,
                            tooltip=f"Kurangi {item.name}",
                            disabled=quantity == 1,
                            key=f"decrease-{item.number}",
                            on_click=lambda _, selected=line: on_change(selected, -1),
                        ),
                        ft.Container(
                            width=28,
                            alignment=ft.Alignment.CENTER,
                            content=ft.Text(str(quantity), weight=ft.FontWeight.BOLD),
                        ),
                        ft.IconButton(
                            icon=ft.Icons.ADD,
                            icon_size=17,
                            tooltip=f"Tambah {item.name}",
                            key=f"increase-{item.number}",
                            on_click=lambda _, selected=line: on_change(selected, 1),
                        ),
                        ft.Container(expand=True),
                        ft.IconButton(
                            icon=ft.Icons.DELETE_OUTLINE,
                            icon_size=19,
                            icon_color=Color.danger,
                            tooltip=f"Hapus {item.name}",
                            key=f"remove-{item.number}",
                            on_click=lambda _, selected=item: on_remove(selected),
                        ),
                    ],
                ),
            ],
        ),
    )
