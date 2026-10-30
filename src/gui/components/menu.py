from collections.abc import Callable

import flet as ft

from gui.theme import MENU_ICONS, Color
from shared.restaurant import MenuItem, rupiah


def section_title(title: str, count: int) -> ft.Row:
    return ft.Row(
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        controls=[
            ft.Text(title, size=18, weight=ft.FontWeight.BOLD, color=Color.ink),
            ft.Text(f"{count} pilihan", size=12, color=Color.muted),
        ],
    )


def menu_card(
    item: MenuItem, on_add: Callable[[MenuItem], None], primary_category: str
) -> ft.Container:
    is_primary_category = item.category == primary_category
    return ft.Container(
        col={"xs": 12, "sm": 6, "lg": 12, "xl": 6},
        padding=16,
        bgcolor=Color.surface,
        border=ft.Border.all(1, Color.line),
        border_radius=12,
        content=ft.Row(
            spacing=13,
            controls=[
                ft.Container(
                    width=48,
                    height=48,
                    border_radius=10,
                    bgcolor=Color.green_light
                    if is_primary_category
                    else Color.amber_light,
                    alignment=ft.Alignment.CENTER,
                    content=ft.Icon(
                        MENU_ICONS.get(item.number, ft.Icons.RESTAURANT),
                        size=25,
                        color=Color.green if is_primary_category else Color.amber,
                    ),
                ),
                ft.Column(
                    expand=True,
                    spacing=3,
                    controls=[
                        ft.Text(
                            item.name,
                            size=15,
                            weight=ft.FontWeight.BOLD,
                            color=Color.ink,
                        ),
                        ft.Text(item.detail, size=12, color=Color.muted),
                        ft.Text(
                            rupiah(item.price),
                            size=14,
                            weight=ft.FontWeight.BOLD,
                            color=Color.green_dark,
                        ),
                    ],
                ),
                ft.IconButton(
                    icon=ft.Icons.ADD,
                    icon_color=Color.surface,
                    bgcolor=Color.green,
                    tooltip=f"Tambah {item.name}",
                    key=f"add-{item.number}",
                    on_click=lambda _, selected=item: on_add(selected),
                ),
            ],
        ),
    )


def menu_sections(
    items: tuple[MenuItem, ...],
    on_add: Callable[[MenuItem], None],
    primary_category: str,
) -> list[ft.Control]:
    menu_sections = []
    for category in dict.fromkeys(item.category for item in items):
        entries = [item for item in items if item.category == category]
        menu_sections.extend(
            [
                section_title(category, len(entries)),
                ft.ResponsiveRow(
                    spacing=10,
                    run_spacing=10,
                    controls=[
                        menu_card(item, on_add, primary_category) for item in entries
                    ],
                ),
            ]
        )

    return menu_sections
