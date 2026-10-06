import flet.testing as ftt


async def test_add_and_pay_exact(flet_app: ftt.FletTestApp):
    tester = flet_app.tester
    await tester.pump_and_settle()

    await tester.tap(await tester.find_by_key("add-1"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("1 item dipilih")).count == 1
    assert (await tester.find_by_text("Rp20.000 / porsi")).count == 1

    await tester.tap(await tester.find_by_key("exact-payment"))
    await tester.pump_and_settle()
    assert (await tester.find_by_text("Pembayaran berhasil")).count == 1
    assert (await tester.find_by_text("Kembalian Rp0")).count == 1
    assert (await tester.find_by_text("0 item dipilih")).count == 1
