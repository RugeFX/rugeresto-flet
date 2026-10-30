"""Receipt history presentation; all values come from the shared core."""

import flet as ft

from gui.theme import Color
from shared.restaurant import Receipt, rupiah


def history_view(
    receipts: tuple[Receipt, ...], selected: Receipt | None, on_select
) -> list[ft.Control]:
    controls = [
        ft.Text(
            "Riwayat transaksi", size=22, weight=ft.FontWeight.BOLD, color=Color.ink
        ),
        ft.Text(
            f"{len(receipts)} transaksi · Penjualan {rupiah(sum(r.total for r in receipts))}",
            color=Color.muted,
        ),
    ]
    if not receipts:
        controls.append(ft.Text("Belum ada pembayaran tersimpan.", color=Color.muted))
    for receipt in reversed(receipts):
        controls.append(
            ft.Container(
                padding=12,
                bgcolor=Color.surface,
                border_radius=10,
                content=ft.Column(
                    controls=[
                        ft.Text(receipt.paid_at, color=Color.muted, size=12),
                        ft.Text(receipt.order_id, selectable=True, size=12),
                        ft.Row(
                            wrap=True,
                            controls=[
                                ft.Text(
                                    rupiah(receipt.total), weight=ft.FontWeight.BOLD
                                ),
                                ft.TextButton(
                                    "Lihat struk",
                                    key=f"receipt-{receipt.order_id}",
                                    on_click=lambda _, paid=receipt: on_select(paid),
                                ),
                            ],
                        ),
                    ]
                ),
            )
        )
    if selected:
        controls.append(ft.Divider(color=Color.line))
        controls.append(ft.Text("Rincian struk", size=18, weight=ft.FontWeight.BOLD))
        controls.append(ft.Text(selected.order_id, selectable=True, size=12))
        for line in selected.lines:
            controls.append(
                ft.Text(
                    f"{line.name} ×{line.quantity} · {rupiah(line.unit_price)} = {rupiah(line.subtotal)}"
                )
            )
        controls.extend(
            [
                ft.Text(f"Total {rupiah(selected.total)}", weight=ft.FontWeight.BOLD),
                ft.Text(
                    f"Dibayar {rupiah(selected.paid)} · Kembalian {rupiah(selected.change)}"
                ),
            ]
        )
    return controls
