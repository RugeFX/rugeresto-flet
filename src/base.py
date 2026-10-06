menu = [
    {"name": "Nasi Goreng", "price": 20000},
    {"name": "Mie Goreng", "price": 18000},
    {"name": "Ayam Goreng", "price": 25000},
    {"name": "Es Teh", "price": 5000},
    {"name": "Es Jeruk", "price": 8000}
]

orders = []


def show_food_menu():
    print("\n======= RESTAURANT MENU =======")

    for number, item in enumerate(menu, start=1):
        print(f"{number}. {item['name']} - Rp{item['price']:,}")

    print("===============================")


def add_order():
    show_food_menu()

    choice = input("Choose menu number: ")

    if not choice.isdigit():
        print("Invalid menu option.")
        return

    choice = int(choice) - 1

    if not 0 <= choice < len(menu):
        print("Menu not found.")
        return

    quantity = input("Enter quantity: ")

    if not quantity.isdigit():
        print("Invalid quantity.")
        return

    quantity = int(quantity)

    if quantity <= 0:
        print("Quantity must be greater than 0.")
        return

    item = menu[choice]

    found = False

    for order in orders:
        if order["name"] == item["name"]:
            order["quantity"] += quantity
            found = True
            break

    if not found:
        order = {
            "name": item["name"],
            "price": item["price"],
            "quantity": quantity
        }

        orders.append(order)

    print(f"{item['name']} x{quantity} added to order.")


def view_order():
    print("\n========== YOUR ORDER ==========")

    total = 0

    for i, order in enumerate(orders, start=1):
        subtotal = order["price"] * order["quantity"]

        print(
            f"{i}. {order['name']} "
            f"x{order['quantity']} "
            f"- Rp{subtotal:,}"
        )

        total += subtotal

    print("--------------------------------")
    print(f"Total: Rp{total:,}")
    print("================================")


def update_order():
    view_order()

    number = input("Choose order number to update: ")

    if not number.isdigit():
        print("Invalid order number.")
        return

    number = int(number)

    if number < 1 or number > len(orders):
        print("Order not found.")
        return

    quantity = input("Enter new quantity: ")

    if not quantity.isdigit():
        print("Invalid quantity.")
        return

    quantity = int(quantity)

    if quantity <= 0:
        print("Quantity must be greater than 0.")
        return

    orders[number - 1]["quantity"] = quantity

    print("Order updated successfully.")


def delete_order():
    view_order()

    number = input("Choose order number to delete: ")

    if not number.isdigit():
        print("Invalid order number.")
        return

    number = int(number)

    if number < 1 or number > len(orders):
        print("Order not found.")
        return

    removed = orders.pop(number - 1)

    print(f"{removed['name']} removed from order.")


def calculate_total():
    total = 0

    for order in orders:
        subtotal = order["price"] * order["quantity"]
        total += subtotal

    return total


def payment():
    view_order()

    total = calculate_total()

    payment_input = input("Enter payment amount: Rp")

    if not payment_input.isdigit():
        print("Invalid payment amount.")
        return

    payment_amount = int(payment_input)

    if payment_amount < total:
        shortage = total - payment_amount

        print("Insufficient payment.")
        print(f"You still need Rp{shortage:,}")
        return

    change = payment_amount - total

    print("\n========== PAYMENT ==========")
    print(f"Total   : Rp{total:,}")
    print(f"Payment : Rp{payment_amount:,}")
    print(f"Change  : Rp{change:,}")
    print("=============================")
    print("Thank you for your order!")

    orders.clear()


def show_main_menu():
    print("\n====== RESTAURANT ORDERING SYSTEM ======")
    print("1. Display Menu")
    print("2. Add Order")
    print("3. View Order")
    print("4. Update Order")
    print("5. Delete Order")
    print("6. Payment")
    print("7. Exit")
    print("========================================")

def run_if_order_exists(fn):
    if len(orders) == 0:
        print("\nYour order is empty.")
        return
    
    fn()

# Main Program
while True:
    show_main_menu()

    choice = input("Choose an option: ")

    if choice == "1":
        show_food_menu()

    elif choice == "2":
        add_order()

    elif choice == "3":
        run_if_order_exists(view_order)

    elif choice == "4":
        run_if_order_exists(update_order)

    elif choice == "5":
        run_if_order_exists(delete_order)

    elif choice == "6":
        run_if_order_exists(payment)

    elif choice == "7" or choice == "exit" or choice == "q":
        print("Program closed.")
        break

    else:
        print("Invalid menu option.")
        continue