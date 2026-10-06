import json
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class MenuItem:
    number: int
    name: str
    price: int
    category: str
    detail: str


MENU_PATH = Path(__file__).with_name("menu.json")


def load_menu(path: Path = MENU_PATH) -> tuple[MenuItem, ...]:
    """Read menu records from JSON, rejecting invalid or duplicate entries."""
    with path.open(encoding="utf-8") as file:
        records = json.load(file)

    if not isinstance(records, list):
        raise TypeError("Menu JSON must contain a list of items")

    items = []
    numbers = set()
    fields = {"number", "name", "price", "category", "detail"}
    for index, record in enumerate(records, start=1):
        if not isinstance(record, dict):
            raise TypeError(f"Menu record {index} must be an object")
        if set(record) != fields:
            raise ValueError(f"Menu record {index} must contain {sorted(fields)}")
        if type(record["number"]) is not int:
            raise TypeError(f"Menu record {index} needs an integer number")
        if record["number"] <= 0:
            raise ValueError(f"Menu record {index} needs a positive integer number")
        if record["number"] in numbers:
            raise ValueError(f"Duplicate menu number: {record['number']}")
        if type(record["price"]) is not int:
            raise TypeError(f"Menu record {index} needs an integer price")
        if record["price"] < 0:
            raise ValueError(f"Menu record {index} needs a non-negative integer price")
        for field in ("name", "category", "detail"):
            if not isinstance(record[field], str):
                raise TypeError(f"Menu record {index} needs a string {field}")
            if not record[field].strip():
                raise ValueError(f"Menu record {index} needs a non-empty {field}")
        items.append(MenuItem(**record))
        numbers.add(record["number"])
    return tuple(items)


MENU = load_menu()
MENU_CATEGORIES = tuple(dict.fromkeys(item.category for item in MENU))
_MENU_BY_NUMBER = {item.number: item for item in MENU}


def rupiah(amount: int) -> str:
    return f"Rp{amount:,}".replace(",", ".")


class RestaurantError(ValueError):
    """A rejected restaurant operation; the order remains unchanged."""


class UnknownMenuItem(RestaurantError):
    pass


class ItemNotOrdered(RestaurantError):
    pass


class InvalidQuantity(RestaurantError):
    pass


class EmptyOrder(RestaurantError):
    pass


class InvalidPayment(RestaurantError):
    pass


class InsufficientPayment(RestaurantError):
    def __init__(self, shortfall: int):
        self.shortfall = shortfall
        super().__init__(f"Payment is short by {shortfall}")


@dataclass(frozen=True, slots=True)
class OrderLine:
    item: MenuItem
    quantity: int

    @property
    def subtotal(self) -> int:
        return self.item.price * self.quantity


@dataclass(frozen=True, slots=True)
class Receipt:
    lines: tuple[OrderLine, ...]
    total: int
    paid: int
    change: int


class RestaurantOrder:
    """One active order. Payment returns a receipt and starts a new order."""

    def __init__(self) -> None:
        self._quantities: dict[int, int] = {}

    @property
    def lines(self) -> tuple[OrderLine, ...]:
        return tuple(
            OrderLine(_MENU_BY_NUMBER[number], quantity)
            for number, quantity in self._quantities.items()
        )

    @property
    def item_count(self) -> int:
        return sum(self._quantities.values())

    @property
    def total(self) -> int:
        return sum(line.subtotal for line in self.lines)

    def add(self, number: int, quantity: int = 1) -> None:
        self._menu_item(number)
        self._positive_quantity(quantity)
        self._quantities[number] = self._quantities.get(number, 0) + quantity

    def set_quantity(self, number: int, quantity: int) -> None:
        self._ordered_item(number)
        self._positive_quantity(quantity)
        self._quantities[number] = quantity

    def change_quantity(self, number: int, difference: int) -> None:
        self._ordered_item(number)
        if type(difference) is not int:
            raise InvalidQuantity("Quantity change must be a whole number")
        self.set_quantity(number, self._quantities[number] + difference)

    def remove(self, number: int) -> None:
        self._ordered_item(number)
        del self._quantities[number]

    def pay(self, amount: int) -> Receipt:
        if not self._quantities:
            raise EmptyOrder("Order is empty")
        if type(amount) is not int or amount < 0:
            raise InvalidPayment("Payment must be a non-negative whole number")

        total = self.total
        if amount < total:
            raise InsufficientPayment(total - amount)

        receipt = Receipt(self.lines, total, amount, amount - total)
        self._quantities.clear()
        return receipt

    @staticmethod
    def _menu_item(number: int) -> MenuItem:
        if type(number) is not int:
            raise UnknownMenuItem(f"Menu item {number!r} does not exist")
        try:
            return _MENU_BY_NUMBER[number]
        except KeyError as exc:
            raise UnknownMenuItem(f"Menu item {number!r} does not exist") from exc

    def _ordered_item(self, number: int) -> None:
        self._menu_item(number)
        if number not in self._quantities:
            raise ItemNotOrdered(f"Menu item {number!r} is not in the order")

    @staticmethod
    def _positive_quantity(quantity: int) -> None:
        if type(quantity) is not int or quantity <= 0:
            raise InvalidQuantity("Quantity must be a positive whole number")
