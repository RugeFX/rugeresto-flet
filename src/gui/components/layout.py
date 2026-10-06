import flet as ft

from gui.theme import Color


def restaurant_layout(
    menu_sections: list[ft.Control], order_panel: ft.Control
) -> ft.Pagelet:
    return ft.Pagelet(
        expand=True,
        bgcolor=Color.background,
        content=ft.SafeArea(
            expand=True,
            content=ft.Column(
                expand=True,
                scroll=ft.ScrollMode.AUTO,
                spacing=0,
                controls=[
                    ft.Container(
                        padding=ft.Padding.symmetric(vertical=17, horizontal=24),
                        bgcolor=Color.surface,
                        border=ft.Border.only(bottom=ft.BorderSide(1, Color.line)),
                        content=ft.Row(
                            spacing=11,
                            controls=[
                                ft.Container(
                                    width=34,
                                    height=34,
                                    alignment=ft.Alignment.CENTER,
                                    bgcolor=Color.green,
                                    border_radius=9,
                                    content=ft.Icon(
                                        ft.Icons.RESTAURANT_MENU,
                                        color=Color.surface,
                                        size=19,
                                    ),
                                ),
                                ft.Text(
                                    "RestoRuge",
                                    size=18,
                                    weight=ft.FontWeight.BOLD,
                                    color=Color.ink,
                                ),
                                ft.Container(expand=True),
                                ft.Text("Pesan & bayar", size=12, color=Color.muted),
                            ],
                        ),
                    ),
                    ft.Container(
                        padding=ft.Padding.symmetric(vertical=30, horizontal=24),
                        content=ft.Column(
                            spacing=24,
                            controls=[
                                ft.Container(
                                    padding=ft.Padding.symmetric(
                                        vertical=26, horizontal=28
                                    ),
                                    bgcolor=Color.green_dark,
                                    border_radius=14,
                                    content=ft.Column(
                                        spacing=6,
                                        controls=[
                                            ft.Text(
                                                "Menu hari ini",
                                                size=12,
                                                weight=ft.FontWeight.BOLD,
                                                color="#BFE6D2",
                                            ),
                                            ft.Text(
                                                "Mau makan apa?",
                                                size=29,
                                                weight=ft.FontWeight.BOLD,
                                                color=Color.surface,
                                            ),
                                            ft.Text(
                                                "Pilih hidangan, atur jumlahnya, lalu selesaikan pembayaran.",
                                                color="#E1F0E7",
                                                size=13,
                                            ),
                                        ],
                                    ),
                                ),
                                ft.ResponsiveRow(
                                    spacing=16,
                                    run_spacing=16,
                                    vertical_alignment=ft.CrossAxisAlignment.START,
                                    controls=[
                                        ft.Container(
                                            col={"xs": 12, "lg": 8},
                                            content=ft.Column(
                                                spacing=14, controls=menu_sections
                                            ),
                                        ),
                                        order_panel,
                                    ],
                                ),
                                ft.Text(
                                    "Harga dalam rupiah · Pembayaran tunai",
                                    size=11,
                                    color=Color.muted,
                                ),
                            ],
                        ),
                    ),
                ],
            ),
        ),
    )
