import csv
import os
import tempfile
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

DATA_DIR = Path(
    os.environ.get("RUGERESTO_DATA_DIR", Path(__file__).resolve().parents[2] / "data")
)
MENU_PATH = DATA_DIR / "menu.csv"
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
                pass  # Preserve the original save result if temp cleanup also fails.


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


def load_menu(path: Path = MENU_PATH) -> tuple[MenuItem, ...]:
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
        raise DataFileError(f"Invalid {path}: the menu must contain at least one item.")
    return tuple(items)


def rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")


class RestaurantSystem:
    """One cashier session with CSV-backed orders and immutable paid receipts.

    Run one application at a time for this data directory.
    """

    def __init__(self, data_dir: Path = DATA_DIR) -> None:
        self.data_dir: Path = Path(data_dir).resolve()
        self.notice: str = ""
        self.refresh()

    def refresh(self) -> None:
        """Reload the CSV files for the current application."""
        menu = self._load_menu()
        receipts = self._load_transactions()
        order_id, orders = self._load_order()
        self.menu: tuple[MenuItem, ...] = menu
        self._menu_by_number = {item.number: item for item in menu}
        self._receipts: tuple[Receipt, ...] = receipts
        self._order_id, self._orders = order_id, orders
        self.notice = ""
        self._recover_paid_order()

    def _load_menu(self) -> tuple[MenuItem, ...]:
        return load_menu(self.data_dir / "menu.csv")

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
        # A durable receipt is authoritative if interruption occurred before cleanup.
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

    def add_order(self, number: int, quantity: int = 1) -> MenuItem:
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

    def change_quantity(self, menu_number: int, difference: int) -> None:
        if type(difference) is not int:
            raise RestaurantError("Quantity change must be a whole number.")
        lines = list(self._orders)
        for index, line in enumerate(lines):
            if type(menu_number) is int and line.menu_number == menu_number:
                quantity = line.quantity + difference
                self._quantity(quantity)
                lines[index] = OrderLine(
                    line.menu_number, line.name, line.unit_price, quantity
                )
                self._commit_order(tuple(lines))
                return
        raise RestaurantError("Item is not in the order.")

    def remove_item(self, menu_number: int) -> None:
        if type(menu_number) is not int or not any(
            line.menu_number == menu_number for line in self._orders
        ):
            raise RestaurantError("Item is not in the order.")
        self._commit_order(
            tuple(line for line in self._orders if line.menu_number != menu_number)
        )

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
        assert self._order_id is not None  # Every durable nonempty order has an ID.
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
        # Commit only after the receipt is durable. Never retry a paid order as unpaid.
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
