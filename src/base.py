import argparse
import csv
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

DATA_DIR = Path(__file__).resolve().parents[1] / "data"
WIB = timezone(timedelta(hours=7), "WIB")
MENU_FIELDS = ("number", "name", "price", "category", "detail")
ORDER_FIELDS = ("order_id", "menu_number", "name", "unit_price", "quantity")
TRANSACTION_FIELDS = (
    "order_id",
    "paid_at",
    "menu_number",
    "name",
    "unit_price",
    "quantity",
    "line_total",
    "order_total",
    "paid",
    "change",
)


class RestaurantError(ValueError):
    """A recoverable input or data error that can be displayed in the terminal."""


class DataFileError(RestaurantError):
    """A file could not be read, validated, or saved safely."""


@dataclass(frozen=True)
class MenuItem:
    number: int
    name: str
    price: int
    category: str
    detail: str


@dataclass(frozen=True)
class OrderLine:
    menu_number: int
    name: str
    unit_price: int
    quantity: int

    @property
    def subtotal(self) -> int:
        return self.unit_price * self.quantity


@dataclass(frozen=True)
class Receipt:
    order_id: str
    paid_at: str
    lines: tuple[OrderLine, ...]
    total: int
    paid: int
    change: int


def normalize_text(text: str) -> str:
    """Strip edges, normalize case, and collapse repeated whitespace."""
    return " ".join(text.strip().lower().split())


def _read_csv(path: Path, fields: tuple[str, ...]) -> list[dict[str, str]]:
    try:
        with path.open(encoding="utf-8-sig", newline="") as file:
            reader = csv.DictReader(file, strict=True)
            if tuple(reader.fieldnames or ()) != fields:
                raise ValueError(f"expected header: {','.join(fields)}")
            rows = []
            for row in reader:
                if set(row) != set(fields) or any(
                    value is None for value in row.values()
                ):
                    raise ValueError(
                        f"row {reader.line_num} has missing or extra fields"
                    )
                rows.append(row)
            return rows
    except (OSError, UnicodeError, csv.Error, ValueError) as error:
        raise DataFileError(
            f"Cannot read {path}: {error}. Check the file, then retry."
        ) from error


def _write_csv(path: Path, fields: tuple[str, ...], rows: list[dict]) -> None:
    """Replace one file only after its complete replacement is written to disk."""
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            newline="",
            dir=path.parent,
            prefix=f".{path.name}.",
            suffix=".tmp",
            delete=False,
        ) as file:
            temporary = Path(file.name)
            writer = csv.DictWriter(file, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temporary, path)
    except (OSError, csv.Error, ValueError) as error:
        raise DataFileError(
            f"Cannot save {path}: {error}. Check write access and retry."
        ) from error
    finally:
        if temporary is not None:
            try:
                temporary.unlink(missing_ok=True)
            except OSError:
                pass


def _text(row: dict[str, str], key: str) -> str:
    value = row[key].strip()
    if not value:
        raise ValueError(f"{key} must not be empty")
    return value


def _integer(row: dict[str, str], key: str, minimum: int = 0) -> int:
    try:
        value = int(row[key])
    except ValueError as error:
        raise ValueError(f"{key} must be a whole number") from error
    if value < minimum:
        raise ValueError(f"{key} must be at least {minimum}")
    return value


def _load_line(row: dict[str, str]) -> OrderLine:
    return OrderLine(
        _integer(row, "menu_number", 1),
        _text(row, "name"),
        _integer(row, "unit_price"),
        _integer(row, "quantity", 1),
    )


def _line_row(line: OrderLine) -> dict:
    return {
        "menu_number": line.menu_number,
        "name": line.name,
        "unit_price": line.unit_price,
        "quantity": line.quantity,
    }


class RestaurantSystem:
    """One cashier session with CSV-backed orders and immutable paid receipts.

    Run one writer per data directory. CSV files are not a multi-process database.
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir: Path = Path(data_dir).resolve()
        self.menu: tuple[MenuItem, ...] = self._load_menu()
        self._menu_by_number = {item.number: item for item in self.menu}
        self._receipts: tuple[Receipt, ...] = self._load_transactions()
        self._order_id: str | None
        self._order_id, self._orders = self._load_order()
        self.notice: str = ""
        self._recover_paid_order()

    def _load_menu(self) -> tuple[MenuItem, ...]:
        path = self.data_dir / "menu.csv"
        rows = _read_csv(path, MENU_FIELDS)
        items = []
        seen = set()
        for index, row in enumerate(rows, 2):
            try:
                number = _integer(row, "number", 1)
                if number in seen:
                    raise ValueError(f"duplicate menu number {number}")
                items.append(
                    MenuItem(
                        number,
                        _text(row, "name"),
                        _integer(row, "price"),
                        _text(row, "category"),
                        _text(row, "detail"),
                    )
                )
                seen.add(number)
            except ValueError as error:
                raise DataFileError(f"Invalid {path}, row {index}: {error}.") from error
        if not items:
            raise DataFileError(
                f"Invalid {path}: the menu must contain at least one item."
            )
        return tuple(items)

    def _load_order(self) -> tuple[str | None, tuple[OrderLine, ...]]:
        path = self.data_dir / "active_order.csv"
        rows = _read_csv(path, ORDER_FIELDS)
        lines = []
        order_id = None
        seen = set()
        for index, row in enumerate(rows, 2):
            try:
                current_id = _text(row, "order_id")
                if order_id is not None and current_id != order_id:
                    raise ValueError("active order contains different order IDs")
                line = _load_line(row)
                if line.menu_number in seen:
                    raise ValueError(
                        f"duplicate ordered menu number {line.menu_number}"
                    )
                seen.add(line.menu_number)
                order_id = current_id
                lines.append(line)
            except ValueError as error:
                raise DataFileError(f"Invalid {path}, row {index}: {error}.") from error
        return order_id, tuple(lines)

    def _load_transactions(self) -> tuple[Receipt, ...]:
        path = self.data_dir / "transactions.csv"
        groups = {}
        for index, row in enumerate(_read_csv(path, TRANSACTION_FIELDS), 2):
            try:
                order_id = _text(row, "order_id")
                paid_at = _text(row, "paid_at")
                timestamp = datetime.fromisoformat(paid_at)
                if timestamp.utcoffset() is None:
                    raise ValueError("paid_at needs an ISO timestamp with a timezone")
                total = _integer(row, "order_total")
                paid = _integer(row, "paid")
                change = _integer(row, "change")
                if paid < total or change != paid - total:
                    raise ValueError(
                        "paid amount and change do not match the order total"
                    )
                line = _load_line(row)
                if line.subtotal != _integer(row, "line_total"):
                    raise ValueError(
                        "line_total does not match price multiplied by quantity"
                    )
                metadata = (paid_at, total, paid, change)
                previous_metadata, lines = groups.setdefault(order_id, (metadata, []))
                if metadata != previous_metadata:
                    raise ValueError(
                        "receipt rows contain inconsistent payment details"
                    )
                if any(previous.menu_number == line.menu_number for previous in lines):
                    raise ValueError("duplicate item in a paid receipt")
                lines.append(line)
            except ValueError as error:
                raise DataFileError(f"Invalid {path}, row {index}: {error}.") from error
        receipts = []
        for order_id, (metadata, lines) in groups.items():
            paid_at, total, paid, change = metadata
            if sum(line.subtotal for line in lines) != total:
                raise DataFileError(
                    f"Invalid {path}: receipt {order_id} has an incorrect total."
                )
            receipts.append(
                Receipt(order_id, paid_at, tuple(lines), total, paid, change)
            )
        return tuple(receipts)

    def _recover_paid_order(self) -> None:
        receipt = next(
            (r for r in self._receipts if r.order_id == self._order_id), None
        )
        if receipt is None:
            return
        if sorted(self._orders, key=lambda line: line.menu_number) != sorted(
            receipt.lines,
            key=lambda line: line.menu_number,
        ):
            raise DataFileError(
                "Saved active order conflicts with its paid receipt. Check the CSV files."
            )

        self._orders = ()
        self._order_id = None
        self.notice = (
            f"Recovered paid receipt {receipt.order_id}; it will not be charged again."
        )
        self._clear_paid_order_file()

    def _clear_paid_order_file(self) -> None:
        try:
            _write_csv(self.data_dir / "active_order.csv", ORDER_FIELDS, [])
        except DataFileError as error:
            self.notice += (
                f" Payment is saved, but order-file cleanup is pending. {error}"
            )

    @property
    def orders(self) -> tuple[OrderLine, ...]:
        return self._orders

    def search_menu(self, query: str) -> tuple[MenuItem, ...]:
        term = normalize_text(query)
        if not term:
            raise RestaurantError("Enter a menu name to search.")
        return tuple(item for item in self.menu if term in normalize_text(item.name))

    def _commit_order(self, lines: tuple[OrderLine, ...]) -> None:
        order_id = (self._order_id or uuid4().hex) if lines else None
        rows = [{"order_id": order_id, **_line_row(line)} for line in lines]
        _write_csv(self.data_dir / "active_order.csv", ORDER_FIELDS, rows)
        self._order_id, self._orders = order_id, lines

    @staticmethod
    def _quantity(quantity: int) -> None:
        if type(quantity) is not int or quantity <= 0:
            raise RestaurantError("Quantity must be a whole number greater than 0.")

    def add_order(self, number: int, quantity: int) -> MenuItem:
        self._quantity(quantity)
        if type(number) is not int or number not in self._menu_by_number:
            raise RestaurantError("Menu not found.")
        item = self._menu_by_number[number]
        lines = list(self._orders)
        for index, line in enumerate(lines):
            if line.menu_number == number:
                lines[index] = OrderLine(
                    number, line.name, line.unit_price, line.quantity + quantity
                )
                break
        else:
            lines.append(OrderLine(number, item.name, item.price, quantity))
        self._commit_order(tuple(lines))
        return item

    def _order_index(self, number: int) -> int:
        if type(number) is not int or not 1 <= number <= len(self._orders):
            raise RestaurantError("Order not found. Choose a row from your order.")
        return number - 1

    def update_order(self, number: int, quantity: int) -> None:
        index = self._order_index(number)
        self._quantity(quantity)
        lines = list(self._orders)
        line = lines[index]
        lines[index] = OrderLine(line.menu_number, line.name, line.unit_price, quantity)
        self._commit_order(tuple(lines))

    def delete_order(self, number: int) -> OrderLine:
        index = self._order_index(number)
        lines = list(self._orders)
        removed = lines.pop(index)
        self._commit_order(tuple(lines))
        return removed

    def calculate_total(self) -> int:
        return sum(line.subtotal for line in self._orders)

    def payment(self, amount: int) -> Receipt:
        if not self._orders:
            raise RestaurantError("Your order is empty.")
        if type(amount) is not int or amount < 0:
            raise RestaurantError("Payment must be a non-negative whole number.")
        total = self.calculate_total()
        if amount < total:
            raise RestaurantError(
                f"Insufficient payment. You still need Rp{total - amount:,}."
            )

        assert self._order_id is not None

        receipt = Receipt(
            self._order_id,
            datetime.now(WIB).isoformat(timespec="seconds"),
            self._orders,
            total,
            amount,
            amount - total,
        )
        receipts = self._receipts + (receipt,)
        rows = [
            {
                "order_id": paid.order_id,
                "paid_at": paid.paid_at,
                **_line_row(line),
                "line_total": line.subtotal,
                "order_total": paid.total,
                "paid": paid.paid,
                "change": paid.change,
            }
            for paid in receipts
            for line in paid.lines
        ]
        _write_csv(self.data_dir / "transactions.csv", TRANSACTION_FIELDS, rows)

        self._receipts = receipts
        self._orders = ()
        self._order_id = None
        self.notice = ""
        self._clear_paid_order_file()
        return receipt

    def get_transactions(self) -> tuple[Receipt, ...]:
        return self._receipts

    def get_receipt(self, order_id: str) -> Receipt:
        for receipt in self._receipts:
            if receipt.order_id == order_id.strip().lower():
                return receipt
        raise RestaurantError(
            "Receipt not found. Copy its full ID from transaction history."
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


def run_cli(system: RestaurantSystem, read=input, write=print) -> None:
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
