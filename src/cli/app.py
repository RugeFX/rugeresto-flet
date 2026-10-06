from collections.abc import Callable

from shared.restaurant import MENU, InsufficientPayment, RestaurantOrder

Read = Callable[[str], str]
Write = Callable[[str], None]


def show_menu(write: Write) -> None:
    write("\n======= RESTAURANT MENU =======")
    for item in MENU:
        write(f"{item.number}. {item.name} - Rp{item.price:,}")
    write("===============================")


def show_order(order: RestaurantOrder, write: Write) -> None:
    write("\n========== YOUR ORDER ==========")
    for number, line in enumerate(order.lines, start=1):
        write(f"{number}. {line.item.name} x{line.quantity} - Rp{line.subtotal:,}")
    write("--------------------------------")
    write(f"Total: Rp{order.total:,}")
    write("================================")


def read_number(read: Read, write: Write, prompt: str, error: str) -> int | None:
    value = read(prompt)
    if not value.isdecimal():
        write(error)
        return None
    return int(value)


def run_cli(read: Read = input, write: Write = print) -> None:
    order = RestaurantOrder()
    while True:
        write("\n====== RESTAURANT ORDERING SYSTEM ======")
        for action in (
            "1. Display Menu",
            "2. Add Order",
            "3. View Order",
            "4. Update Order",
            "5. Delete Order",
            "6. Payment",
            "7. Exit",
        ):
            write(action)
        write("========================================")
        try:
            choice = read("Choose an option: ")
            if choice in ("7", "exit", "q"):
                write("Program closed.")
                return
            if choice == "1":
                show_menu(write)
            elif choice == "2":
                show_menu(write)
                number = read_number(
                    read, write, "Choose menu number: ", "Invalid menu option."
                )
                if number is None:
                    continue
                item = next((item for item in MENU if item.number == number), None)
                if item is None:
                    write("Menu not found.")
                    continue
                quantity = read_number(
                    read, write, "Enter quantity: ", "Invalid quantity."
                )
                if quantity is None:
                    continue
                if quantity <= 0:
                    write("Quantity must be greater than 0.")
                    continue
                order.add(number, quantity)
                write(f"{item.name} x{quantity} added to order.")
            elif choice in ("3", "4", "5", "6"):
                if not order.lines:
                    write("\nYour order is empty.")
                    continue
                show_order(order, write)
                if choice in ("4", "5"):
                    verb = "update" if choice == "4" else "delete"
                    number = read_number(
                        read,
                        write,
                        f"Choose order number to {verb}: ",
                        "Invalid order number.",
                    )
                    if number is None:
                        continue
                    if not 1 <= number <= len(order.lines):
                        write("Order not found.")
                        continue
                    item = order.lines[number - 1].item
                    if choice == "5":
                        order.remove(item.number)
                        write(f"{item.name} removed from order.")
                    else:
                        quantity = read_number(
                            read, write, "Enter new quantity: ", "Invalid quantity."
                        )
                        if quantity is None:
                            continue
                        if quantity <= 0:
                            write("Quantity must be greater than 0.")
                            continue
                        order.set_quantity(item.number, quantity)
                        write("Order updated successfully.")
                elif choice == "6":
                    amount = read_number(
                        read,
                        write,
                        "Enter payment amount: Rp",
                        "Invalid payment amount.",
                    )
                    if amount is None:
                        continue
                    try:
                        receipt = order.pay(amount)
                    except InsufficientPayment as error:
                        write("Insufficient payment.")
                        write(f"You still need Rp{error.shortfall:,}")
                        continue
                    write("\n========== PAYMENT ==========")
                    write(f"Total   : Rp{receipt.total:,}")
                    write(f"Payment : Rp{receipt.paid:,}")
                    write(f"Change  : Rp{receipt.change:,}")
                    write("=============================")
                    write("Thank you for your order!")
            else:
                write("Invalid menu option.")
        except (EOFError, KeyboardInterrupt):
            write("\nProgram closed.")
            return
