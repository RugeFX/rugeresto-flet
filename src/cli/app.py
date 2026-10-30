"""Terminal adapter for the shared CSV restaurant core."""

import argparse
from pathlib import Path

from shared.restaurant import (
    DATA_DIR,
    DataFileError,
    MenuItem,
    Receipt,
    RestaurantError,
    RestaurantSystem,
    normalize_text,
)


def show_food_menu(items: tuple[MenuItem, ...], write=print) -> None:
    write("\n======= RESTAURANT MENU =======")
    for item in items:
        write(f"{item.number}. {item.name} - Rp{item.price:,}")
    write("===============================")


def view_order(system: RestaurantSystem, write=print) -> None:
    write("\n========== YOUR ORDER ==========")
    for number, line in enumerate(system.orders, 1):
        write(f"{number}. {line.name} x{line.quantity} - Rp{line.subtotal:,}")
    write("--------------------------------")
    write(f"Total: Rp{system.calculate_total():,}")
    write("================================")


def show_receipt(receipt: Receipt, write=print) -> None:
    write("\n========== PAYMENT ==========")
    write(f"Receipt : {receipt.order_id}")
    write(f"Time    : {receipt.paid_at}")
    for line in receipt.lines:
        write(f"{line.name} x{line.quantity} - Rp{line.subtotal:,}")
    write(f"Total   : Rp{receipt.total:,}")
    write(f"Payment : Rp{receipt.paid:,}")
    write(f"Change  : Rp{receipt.change:,}")
    write("=============================")


def run_cli(system: RestaurantSystem | None = None, read=input, write=print) -> None:
    if system is None:
        system = RestaurantSystem()
    if system.notice:
        write(system.notice)
    if system.orders:
        write(f"Restored {len(system.orders)} saved order line(s).")
    while True:
        write("\n====== RESTAURANT ORDERING SYSTEM ======")
        for text in (
            "1. Display Menu",
            "2. Add Order",
            "3. View Order",
            "4. Update Order",
            "5. Delete Order",
            "6. Payment",
            "7. Search Menu",
            "8. Transaction History",
            "9. View Receipt",
            "10. Exit",
        ):
            write(text)
        write("========================================")
        try:
            choice = normalize_text(read("Choose an option: "))
            if choice in ("10", "exit", "q"):
                write("Program closed.")
                return
            if choice in ("3", "4", "5", "6") and not system.orders:
                write("\nYour order is empty.")
                continue
            if choice == "1":
                show_food_menu(system.menu, write)
            elif choice == "2":
                show_food_menu(system.menu, write)
                number = int(read("Choose menu number: ").strip())
                quantity = int(read("Enter quantity: ").strip())
                item = system.add_order(number, quantity)
                write(f"{item.name} x{quantity} added to order.")
            elif choice == "3":
                view_order(system, write)
            elif choice == "4":
                view_order(system, write)
                number = int(read("Choose order number to update: ").strip())
                quantity = int(read("Enter new quantity: ").strip())
                system.update_order(number, quantity)
                write("Order updated successfully.")
            elif choice == "5":
                view_order(system, write)
                number = int(read("Choose order number to delete: ").strip())
                removed = system.delete_order(number)
                write(f"{removed.name} removed from order.")
            elif choice == "6":
                view_order(system, write)
                amount = int(read("Enter payment amount: Rp").strip())
                receipt = system.payment(amount)
                show_receipt(receipt, write)
                write("Thank you for your order!")
                if system.notice:
                    write(system.notice)
            elif choice == "7":
                matches = system.search_menu(read("Search menu name: "))
                if matches:
                    show_food_menu(matches, write)
                else:
                    write("No matching menu items. Try part of a menu name.")
            elif choice == "8":
                receipts = system.get_transactions()
                if not receipts:
                    write("No paid transactions yet.")
                for receipt in receipts:
                    write(
                        f"{receipt.order_id} | {receipt.paid_at} | Rp{receipt.total:,}"
                    )
                write(
                    f"Transactions: {len(receipts)} | Sales: Rp{sum(r.total for r in receipts):,}"
                )
            elif choice == "9":
                show_receipt(system.get_receipt(read("Receipt ID: ")), write)
            else:
                write("Invalid menu option. Choose 1-10, exit, or q.")
        except (EOFError, KeyboardInterrupt):
            write("\nProgram closed. Saved order changes are retained.")
            return
        except RestaurantError as error:
            write(str(error))
        except ValueError:
            write("Enter a whole number without currency symbols or separators.")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="CSV-backed restaurant ordering system"
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=DATA_DIR,
        help="Directory containing the three CSV files",
    )
    args = parser.parse_args(argv)
    while True:
        try:
            system = RestaurantSystem(args.data_dir)
            break
        except DataFileError as error:
            print(error)
            try:
                choice = normalize_text(
                    input("Fix the file and type retry, or q to exit: ")
                )
            except (EOFError, KeyboardInterrupt):
                return 1
            if choice not in ("retry", "r"):
                return 1
    run_cli(system)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
